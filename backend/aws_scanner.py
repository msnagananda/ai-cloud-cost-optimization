import json
import shutil
import subprocess
from datetime import date, timedelta
from typing import Any


class AWSError(Exception):
    pass


class AWSCLINotFoundError(AWSError):
    pass


class AWSCredentialsError(AWSError):
    pass


class AWSPermissionError(AWSError):
    pass


def _run(args: list[str], region: str | None = None) -> dict:
    if not shutil.which("aws"):
        raise AWSCLINotFoundError(
            "AWS CLI is not installed. Install it from https://aws.amazon.com/cli/"
        )

    cmd = args.copy()
    if region:
        cmd += ["--region", region]
    cmd += ["--output", "json"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise AWSError(f"AWS CLI command timed out: {' '.join(cmd)}")

    if result.returncode != 0:
        err = result.stderr.lower()
        if "unable to locate credentials" in err or "no credentials" in err:
            raise AWSCredentialsError(
                "AWS credentials not configured. Run `aws configure` to set them up."
            )
        if "accessdenied" in err or "not authorized" in err or "unauthorized" in err:
            raise AWSPermissionError(
                f"Insufficient IAM permissions for: {' '.join(args[:3])}. "
                "Ensure the IAM user/role has the required read permissions."
            )
        raise AWSError(f"AWS CLI error: {result.stderr.strip()}")

    return json.loads(result.stdout) if result.stdout.strip() else {}


def get_enabled_regions() -> list[str]:
    data = _run(["aws", "ec2", "describe-regions", "--all-regions"])
    regions = [
        r["RegionName"]
        for r in data.get("Regions", [])
        if r.get("OptInStatus") in ("opt-in-not-required", "opted-in")
    ]
    return sorted(regions)


def get_active_services() -> list[str]:
    today = date.today()
    start = date(today.year, today.month, 1).isoformat()
    end = today.isoformat()
    if start == end:
        start = (today - timedelta(days=1)).isoformat()

    data = _run([
        "aws", "ce", "get-cost-and-usage",
        "--time-period", f"Start={start},End={end}",
        "--granularity", "MONTHLY",
        "--metrics", "UnblendedCost",
        "--group-by", "Type=DIMENSION,Key=SERVICE",
    ])

    services = []
    for result in data.get("ResultsByTime", []):
        for group in result.get("Groups", []):
            amount = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0"))
            if amount > 0:
                services.append(group["Keys"][0])
    return services


def _tags_for(resource_arn: str, region: str) -> dict:
    try:
        data = _run(["aws", "resourcegroupstaggingapi", "get-resources",
                     "--resource-arn-list", resource_arn], region=region)
        tags = {}
        for rm in data.get("ResourceTagMappingList", []):
            for tag in rm.get("Tags", []):
                tags[tag["Key"]] = tag["Value"]
        return tags
    except AWSError:
        return {}


# ---------------------------------------------------------------------------
# Per-service scanners
# Each returns a list of resource dicts with keys:
#   resource_type, id, name, config, tags
# ---------------------------------------------------------------------------

def _scan_ec2(region: str) -> list[dict]:
    data = _run(["aws", "ec2", "describe-instances", "--region", region])
    resources = []
    for reservation in data.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            name = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), inst["InstanceId"])
            tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
            resources.append({
                "resource_type": "EC2 Instance",
                "id": inst["InstanceId"],
                "name": name,
                "config": {
                    "instance_type": inst.get("InstanceType"),
                    "state": inst.get("State", {}).get("Name"),
                    "launch_time": str(inst.get("LaunchTime", "")),
                    "availability_zone": inst.get("Placement", {}).get("AvailabilityZone"),
                    "public_ip": inst.get("PublicIpAddress"),
                    "private_ip": inst.get("PrivateIpAddress"),
                    "platform": inst.get("Platform", "linux"),
                    "monitoring": inst.get("Monitoring", {}).get("State"),
                },
                "tags": tags,
            })
    return resources


def _scan_ebs(region: str) -> list[dict]:
    data = _run(["aws", "ec2", "describe-volumes", "--region", region])
    resources = []
    for vol in data.get("Volumes", []):
        name = next((t["Value"] for t in vol.get("Tags", []) if t["Key"] == "Name"), vol["VolumeId"])
        tags = {t["Key"]: t["Value"] for t in vol.get("Tags", [])}
        resources.append({
            "resource_type": "EBS Volume",
            "id": vol["VolumeId"],
            "name": name,
            "config": {
                "size_gb": vol.get("Size"),
                "volume_type": vol.get("VolumeType"),
                "state": vol.get("State"),
                "iops": vol.get("Iops"),
                "throughput": vol.get("Throughput"),
                "encrypted": vol.get("Encrypted"),
                "attachments": [a.get("InstanceId") for a in vol.get("Attachments", [])],
            },
            "tags": tags,
        })
    return resources


def _scan_rds(region: str) -> list[dict]:
    data = _run(["aws", "rds", "describe-db-instances", "--region", region])
    resources = []
    for db in data.get("DBInstances", []):
        tags = {}
        try:
            tag_data = _run(["aws", "rds", "list-tags-for-resource",
                              "--resource-name", db.get("DBInstanceArn", ""), "--region", region])
            tags = {t["Key"]: t["Value"] for t in tag_data.get("TagList", [])}
        except AWSError:
            pass
        resources.append({
            "resource_type": "RDS Instance",
            "id": db["DBInstanceIdentifier"],
            "name": db["DBInstanceIdentifier"],
            "config": {
                "engine": db.get("Engine"),
                "engine_version": db.get("EngineVersion"),
                "instance_class": db.get("DBInstanceClass"),
                "status": db.get("DBInstanceStatus"),
                "storage_gb": db.get("AllocatedStorage"),
                "storage_type": db.get("StorageType"),
                "multi_az": db.get("MultiAZ"),
                "publicly_accessible": db.get("PubliclyAccessible"),
            },
            "tags": tags,
        })
    return resources


def _scan_s3() -> list[dict]:
    data = _run(["aws", "s3api", "list-buckets"])
    resources = []
    for bucket in data.get("Buckets", []):
        name = bucket["Name"]
        tags = {}
        try:
            tag_data = _run(["aws", "s3api", "get-bucket-tagging", "--bucket", name])
            tags = {t["Key"]: t["Value"] for t in tag_data.get("TagSet", [])}
        except AWSError:
            pass

        location = {}
        try:
            loc_data = _run(["aws", "s3api", "get-bucket-location", "--bucket", name])
            location = {"region": loc_data.get("LocationConstraint") or "us-east-1"}
        except AWSError:
            pass

        resources.append({
            "resource_type": "S3 Bucket",
            "id": name,
            "name": name,
            "config": {
                "creation_date": str(bucket.get("CreationDate", "")),
                **location,
            },
            "tags": tags,
        })
    return resources


def _scan_lambda(region: str) -> list[dict]:
    data = _run(["aws", "lambda", "list-functions", "--region", region])
    resources = []
    for fn in data.get("Functions", []):
        tags = {}
        try:
            tag_data = _run(["aws", "lambda", "list-tags",
                              "--resource", fn.get("FunctionArn", ""), "--region", region])
            tags = tag_data.get("Tags", {})
        except AWSError:
            pass
        resources.append({
            "resource_type": "Lambda Function",
            "id": fn["FunctionName"],
            "name": fn["FunctionName"],
            "config": {
                "runtime": fn.get("Runtime"),
                "memory_mb": fn.get("MemorySize"),
                "timeout_s": fn.get("Timeout"),
                "code_size_bytes": fn.get("CodeSize"),
                "last_modified": fn.get("LastModified"),
                "architecture": fn.get("Architectures", []),
            },
            "tags": tags,
        })
    return resources


def _scan_elb(region: str) -> list[dict]:
    resources = []
    # Application/Network/Gateway load balancers
    try:
        data = _run(["aws", "elbv2", "describe-load-balancers", "--region", region])
        for lb in data.get("LoadBalancers", []):
            tags = {}
            try:
                tag_data = _run(["aws", "elbv2", "describe-tags",
                                  "--resource-arns", lb["LoadBalancerArn"], "--region", region])
                for td in tag_data.get("TagDescriptions", []):
                    tags = {t["Key"]: t["Value"] for t in td.get("Tags", [])}
            except AWSError:
                pass
            resources.append({
                "resource_type": "Elastic Load Balancer",
                "id": lb["LoadBalancerArn"].split("/")[-1],
                "name": lb.get("LoadBalancerName"),
                "config": {
                    "type": lb.get("Type"),
                    "scheme": lb.get("Scheme"),
                    "state": lb.get("State", {}).get("Code"),
                    "dns_name": lb.get("DNSName"),
                    "vpc_id": lb.get("VpcId"),
                },
                "tags": tags,
            })
    except AWSError:
        pass
    return resources


def _scan_nat_gateways(region: str) -> list[dict]:
    data = _run(["aws", "ec2", "describe-nat-gateways", "--region", region])
    resources = []
    for gw in data.get("NatGateways", []):
        tags = {t["Key"]: t["Value"] for t in gw.get("Tags", [])}
        name = tags.get("Name", gw["NatGatewayId"])
        resources.append({
            "resource_type": "NAT Gateway",
            "id": gw["NatGatewayId"],
            "name": name,
            "config": {
                "state": gw.get("State"),
                "vpc_id": gw.get("VpcId"),
                "subnet_id": gw.get("SubnetId"),
                "connectivity_type": gw.get("ConnectivityType"),
            },
            "tags": tags,
        })
    return resources


def _scan_elasticache(region: str) -> list[dict]:
    data = _run(["aws", "elasticache", "describe-cache-clusters",
                 "--show-cache-node-info", "--region", region])
    resources = []
    for cluster in data.get("CacheClusters", []):
        resources.append({
            "resource_type": "ElastiCache Cluster",
            "id": cluster["CacheClusterId"],
            "name": cluster["CacheClusterId"],
            "config": {
                "engine": cluster.get("Engine"),
                "engine_version": cluster.get("EngineVersion"),
                "node_type": cluster.get("CacheNodeType"),
                "num_nodes": cluster.get("NumCacheNodes"),
                "status": cluster.get("CacheClusterStatus"),
            },
            "tags": {},
        })
    return resources


def _scan_cloudfront() -> list[dict]:
    data = _run(["aws", "cloudfront", "list-distributions"])
    resources = []
    for dist in data.get("DistributionList", {}).get("Items", []):
        resources.append({
            "resource_type": "CloudFront Distribution",
            "id": dist["Id"],
            "name": dist.get("DomainName"),
            "config": {
                "status": dist.get("Status"),
                "enabled": dist.get("Enabled"),
                "origins": [o.get("DomainName") for o in dist.get("Origins", {}).get("Items", [])],
                "price_class": dist.get("PriceClass"),
            },
            "tags": {},
        })
    return resources


def _scan_dynamodb(region: str) -> list[dict]:
    data = _run(["aws", "dynamodb", "list-tables", "--region", region])
    resources = []
    for table_name in data.get("TableNames", []):
        try:
            desc = _run(["aws", "dynamodb", "describe-table",
                         "--table-name", table_name, "--region", region])
            table = desc.get("Table", {})
            tags = {}
            try:
                tag_data = _run(["aws", "dynamodb", "list-tags-of-resource",
                                  "--resource-arn", table.get("TableArn", ""), "--region", region])
                tags = {t["Key"]: t["Value"] for t in tag_data.get("Tags", [])}
            except AWSError:
                pass
            resources.append({
                "resource_type": "DynamoDB Table",
                "id": table_name,
                "name": table_name,
                "config": {
                    "status": table.get("TableStatus"),
                    "item_count": table.get("ItemCount"),
                    "size_bytes": table.get("TableSizeBytes"),
                    "billing_mode": table.get("BillingModeSummary", {}).get("BillingMode", "PROVISIONED"),
                    "read_capacity": table.get("ProvisionedThroughput", {}).get("ReadCapacityUnits"),
                    "write_capacity": table.get("ProvisionedThroughput", {}).get("WriteCapacityUnits"),
                },
                "tags": tags,
            })
        except AWSError:
            pass
    return resources


# Maps Cost Explorer service name fragments → scanner function
_SERVICE_SCANNERS: dict[str, Any] = {
    "Amazon Elastic Compute Cloud": [
        ("ec2", _scan_ec2),
        ("ebs", _scan_ebs),
    ],
    "Amazon EC2": [
        ("ec2", _scan_ec2),
        ("ebs", _scan_ebs),
    ],
    "Amazon Relational Database Service": [("rds", _scan_rds)],
    "Amazon Simple Storage Service": [("s3", _scan_s3)],
    "AWS Lambda": [("lambda", _scan_lambda)],
    "Amazon ElastiCache": [("elasticache", _scan_elasticache)],
    "Amazon CloudFront": [("cloudfront", _scan_cloudfront)],
    "Amazon DynamoDB": [("dynamodb", _scan_dynamodb)],
    "Elastic Load Balancing": [("elb", _scan_elb)],
    "Amazon Virtual Private Cloud": [("nat", _scan_nat_gateways)],
}


def scan_active_resources(region: str) -> dict:
    active_services = get_active_services()
    scanned: set[str] = set()
    resources: list[dict] = []
    matched_services: list[str] = []

    for service_name in active_services:
        for pattern, scanners in _SERVICE_SCANNERS.items():
            if pattern.lower() in service_name.lower() or service_name.lower() in pattern.lower():
                for scanner_key, scanner_fn in scanners:
                    if scanner_key in scanned:
                        continue
                    scanned.add(scanner_key)
                    matched_services.append(service_name)
                    try:
                        # S3 and CloudFront are global — no region arg
                        if scanner_fn in (_scan_s3, _scan_cloudfront):
                            results = scanner_fn()
                        else:
                            results = scanner_fn(region)
                        resources.extend(results)
                    except AWSError as e:
                        resources.append({
                            "resource_type": f"Scan Error ({scanner_key})",
                            "id": scanner_key,
                            "name": scanner_key,
                            "config": {"error": str(e)},
                            "tags": {},
                        })

    return {
        "region": region,
        "active_services": active_services,
        "matched_services": list(set(matched_services)),
        "resources": resources,
        "total_resources": len([r for r in resources if "Error" not in r.get("resource_type", "")]),
    }

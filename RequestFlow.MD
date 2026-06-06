## AI Cloud Cost Detective - Request Flow

```
①  User ─·─·─► React ─·─·─► FastAPI Auth ─·─·─► JWT (Azure PostgreSQL)

②  User selects Resource Group ─·─·─► Python Backend

③  Python ─·─·─► AWS CLI (`aws ce get-cost-and-usage`) ─·─·─► Filters for unblended costs

④  Python builds dynamic execution list of active services (e.g., ["AmazonEC2", "AmazonRDS"])

⑤  Python executes CLI `describe` subprocesses *only* for those active services

⑥  Python ─·─·─► FastAPI WebSocket ─·─·─► React (live updates for active components)

⑦  Python ─·─·─► OpenAI API ─·─·─► Precise cost & metadata analysis

⑧  React ◄·─·─·─ Final report with localized optimization suggestions
```

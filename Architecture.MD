## AI Cloud Cost Detective - Architecture

```
                              ┌──────────────┐
                              │     USER     │
                              └──────┬───────┘
                                     │
                                     ▼
                           ┌───────────────────┐
                           │  REACT FRONTEND   │
                           └────────┬──────────┘
                                    :
                                    : Login / Signup
                                    ▼
                           ┌───────────────────┐
                           │  PYTHON BACKEND   │
                           │    (FastAPI)      │
                           │                   │
                           │  · Custom JWT Auth│
                           └───┬───────┬───┬───┘
                               :       :   :
                ┌──────────────┘       :   └──────────────┐
                :                      :                  :
                ▼                      ▼                  ▼
         ┌─────────────--┐     ┌──────────────┐    ┌──────────────┐
         │  AWS   CLI    │     │   FASTAPI    │    │   OLAMA      │
         │               │     │  WEBSOCKET   │    │    API       │
         │aws ce get-cost|     |              |    |              | 
         |               │     |   (Progress) │    │              │
         │               │     └──────┬───────┘    │ Cost Analysis│
         └──────┬──────--┘            :            └──────┬───────┘
                :                     : Live updates      :
                ▼                     ▼                   :
         ┌─────────────-┐   ┌───────────────┐             :
         │   Active AWS |   │   REACT       │             :
         │ Services only│   │  (Progress    │             :
         │              │   |   Tracker)    │             :
         └─────────────-|   └───────────────┘             :
                                                          ▼
                                                 ┌──────────────┐
                                                 │ dockerized   │
                                                 │  POSTGRESQL  │
                                                 │              │
                                                 │              │
                                                 │ · users      │
                                                 │ · analyses   │
                                                 └──────┬───────┘
                                                        :
                                                        : Stored results
                                                        ▼
                                                 ┌───────────────┐
                                                 │    REACT      │
                                                 │ (Final Report │
                                                 │  + Suggestions│
                                                 │  + Fixes)     │
                                                 └───────────────┘
```

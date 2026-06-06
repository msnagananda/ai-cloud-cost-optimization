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
         │  AWS   CLI    │     │   FASTAPI    │    │   OPENAI     │
         │               │     │  WEBSOCKET   │    │    API       │
         │aws ce get-cost|     |              |    |              | 
         |and usage      │     │  (Progress)  │    │              │
         │ list --rg     │     └──────┬───────┘    │ Cost Analysis│
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
                                                 │    AWS RDS   │
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

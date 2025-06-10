# AlgoFinStatiX Backend

Backend service for the AlgoFinStatiX application.

## Development

### Setup

1. Clone the repository
2. Install dependencies: `pip install -e .[dev]`
3. Install postgresql: `sudo apt install postgresql`
4. Set up environment variables (copy `.env.example` to `.env` and configure)
5. Set up database: `python -m scripts.setup.setup_db`
6. Run the application: `uvicorn src.main:app --reload`

### Testing

Run tests with:

```bash
pytest
```

## License

Proprietary - All rights reserved.

# Quick Start Guide - Iterable Integration

## 5-Minute Setup

### Step 1: Install Dependencies (1 minute)
```bash
pip install -r requirements.txt
```

### Step 2: Configure Credentials (2 minutes)
```bash
cp .env.example .env
# Edit .env and add:
# - Database credentials (host, user, password, database)
# - Iterable API key
```

### Step 3: Setup Database (1 minute)
```bash
mysql -u root -p < database_setup.sql
```

### Step 4: Run Integration (1 minute)
```bash
python main.py
```

---

## What Happens When You Run main.py

1. ✅ Loads .env configuration
2. ✅ Connects to your SQL database
3. ✅ Executes Phase 2 Query 2 (finds pro users with recent engagement)
4. ✅ For each user, makes 2 API calls:
   - `POST /api/users/update` - Updates user profile
   - `POST /api/events/track` - Tracks page_view event
5. ✅ Logs all operations to console and file
6. ✅ Saves detailed results to JSON

---

## Output Files Generated

| File | Purpose |
|------|---------|
| `iterable_integration.log` | Debug logs with all operations |
| `integration_results_*.json` | Detailed API responses (timestamped) |
| Console output | Real-time progress |

---

## Verify It Works

After running, you should see:

```
✓ Successfully processed user: sarah.johnson@email.com
✓ Successfully processed user: olivia.brown@email.com
✓ Successfully processed user: mia.harris@email.com

INTEGRATION SUMMARY
Total users processed: 3
✓ Successful (both API calls): 3
```

---

## Common Issues

### "Cannot connect to database"
- Ensure MySQL is running: `mysql -u root -p`
- Check .env credentials
- Run database setup: `mysql -u root -p < database_setup.sql`

### "Missing required environment variables"
- Copy template: `cp .env.example .env`
- Fill in all variables
- No spaces around `=` in .env

### "No pro users found"
- Data might be outside 7-day window
- Verify data exists: `SELECT * FROM customers WHERE plan_type='pro';`
- Re-run database setup

---

## Next Steps

- Review `README.md` for detailed documentation
- Check `integration_results_*.json` for API responses
- Examine `iterable_integration.log` for debug details
- See [README.md](README.md) for advanced configuration

---

**Ready to go!** 🚀

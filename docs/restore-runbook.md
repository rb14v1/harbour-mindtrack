# Database Restore Runbook — mindtrack_harb

Covers the Azure Database for PostgreSQL Flexible Server `psql-mind-test-2`
(resource group `mind-test-2`, region `uksouth`) defined in `infra/main.tf`.

## Backup configuration

| Setting | Value | Source |
|---|---|---|
| Automated backups | Enabled (Azure-managed, daily snapshot + continuous WAL) | Flexible Server default |
| Retention | 30 days | `backup_retention_days = 30` |
| Point-in-time recovery (PITR) | Any point within the 30-day window | Built in to Flexible Server |
| Off-region copy | Geo-redundant backup to the paired region (`ukwest`) | `geo_redundant_backup_enabled = true` |

> `geo_redundant_backup_enabled` can only be set when the server is created. Turning it on
> forces Terraform to recreate the server, so it must be applied **before** go-live data exists.

Azure restores always go to a **new** server. The source server is not changed.

## Prerequisites

- Azure CLI (`az`) signed in with Contributor rights on resource group `mind-test-2`.
- The target time in UTC (ISO 8601), e.g. `2026-11-04T09:30:00Z`. It must fall inside the
  retention window: run `az postgres flexible-server show` and look at `backup.earliestRestoreDate`.

## 1. Point-in-time restore (same region)

Use this to recover from data corruption, a bad migration, or accidental deletes.

```bash
az postgres flexible-server restore \
  --resource-group mind-test-2 \
  --name psql-mind-test-2-restore-<yyyymmddhhmm> \
  --source-server psql-mind-test-2 \
  --restore-time "<UTC ISO-8601 timestamp>"
```

## 2. Geo-restore (regional outage)

Use this when `uksouth` is unavailable. It restores the most recent geo-replicated backup into
the paired region (`ukwest`). Expect an RPO of up to about 1 hour.

```bash
az postgres flexible-server geo-restore \
  --resource-group mind-test-2 \
  --name psql-mind-test-2-georestore \
  --source-server psql-mind-test-2 \
  --location ukwest
```

## 3. Post-restore steps

1. **Networking:** the restored server needs private access. Create a private endpoint for it,
   following `azurerm_private_endpoint.postgresql_pe` in `infra/main.tf`, in the
   `privatelink.postgres.database.azure.com` DNS zone. For a geo-restore, the private endpoint
   must sit on a subnet in the target region.
2. **Validate data:** connect from inside the VNet and check row counts and the latest
   timestamps on key tables, for example `django_migrations` and the application tables.
3. **Repoint the backend:** change the backend's database host setting (env / app settings) to
   the restored server's FQDN, then restart the backend-api.
4. **Smoke test:** confirm `/healthz` returns 200 and the main API flows work.
5. **Reconcile Terraform:** either import the restored server into state in place of the
   original, or move the data back onto the Terraform-managed server with
   `pg_dump`/`pg_restore`. Then delete the temporary server.

## 4. Restore test (required before go-live, then at least once a year)

1. Do a PITR (section 1) to a throwaway server, with a target time about 15 minutes in the past.
2. Run the validation in section 3, step 2, against the restored server.
3. Record the result below, then delete the throwaway server.

| Date (UTC) | Type (PITR / geo) | Restore time target | Duration | Validated by | Result |
|---|---|---|---|---|---|
| _pending — fill in at pre-go-live test_ | | | | | |

ALTER TABLE staging.stg_orders
ADD COLUMN IF NOT EXISTS source_updated_at TIMESTAMPTZ;
UPDATE sessions s
SET purchased = TRUE,
    transaction_id = p.transaction_id
FROM pos_transactions p
WHERE s.store_id = p.store_id
  AND s.purchased = FALSE
  AND s.zones_visited::text ILIKE '%billing%';

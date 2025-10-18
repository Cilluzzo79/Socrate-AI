-- List all documents for user
SELECT id, filename, created_at, status, total_chunks
FROM documents
WHERE user_id = '2d63181a-b335-4536-9501-f369d8ba0d9b'
ORDER BY created_at DESC;

-- Delete all documents except the most recent one
-- UNCOMMENT the lines below after verifying the SELECT output above

-- DELETE FROM documents
-- WHERE user_id = '2d63181a-b335-4536-9501-f369d8ba0d9b'
-- AND id NOT IN (
--     SELECT id FROM documents
--     WHERE user_id = '2d63181a-b335-4536-9501-f369d8ba0d9b'
--     ORDER BY created_at DESC
--     LIMIT 1
-- );

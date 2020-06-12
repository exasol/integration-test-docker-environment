echo 'Running with --host-working-directory "$PWD"'
echo
(./start-test-env spawn-test-environment  --environment-name test --host-working-directory "$PWD" 2>&1 || echo "Failed") | grep -E "SpawnTestContainer|Failed"

echo
echo 'Running without --host-working-directory'
echo

(./start-test-env spawn-test-environment  --environment-name test 2>&1 || echo "Failed") | grep -E "SpawnTestContainer|Failed"

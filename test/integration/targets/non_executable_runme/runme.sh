cat > test/integration/targets/non_executable_script/runme.sh <<EOF
#!/bin/bash
echo "This should fail"
EOF
chmod -x test/integration/targets/non_executable_script/runme.sh

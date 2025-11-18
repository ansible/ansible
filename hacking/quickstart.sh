#!/usr/bin/env bash
# Copyright: (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Ansible Development Environment Quick Start
#
# This script automates the setup process for new Ansible contributors by:
# - Checking system requirements (Python, pip, git)
# - Setting up the development environment
# - Installing dependencies
# - Verifying the installation
# - Providing clear next steps
#
# Usage:
#   ./hacking/quickstart.sh              # Interactive mode with prompts
#   ./hacking/quickstart.sh --silent     # Non-interactive mode for CI/CD
#   ./hacking/quickstart.sh --help       # Show usage information

set -eo pipefail

# Color codes for output
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSIBLE_ROOT="$(dirname "$SCRIPT_DIR")"
REQUIRED_PYTHON_VERSION="3.12"
SILENT_MODE=false
SKIP_VENV=false
SKIP_TESTS=false

# Output functions
print_header() {
    echo ""
    echo "============================================================"
    echo "  Ansible Development Environment Quick Start"
    echo "============================================================"
    echo ""
}

print_step() {
    echo ""
    echo "${BLUE}[$1]${NC} $2"
}

print_success() {
    echo -e "  ${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "  ${RED}[ERROR]${NC} $1" >&2
}

print_warning() {
    echo -e "  ${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}[INFO]${NC} $1"
}

# Version comparison function
version_ge() {
    # Returns 0 if version $1 >= $2, 1 otherwise
    printf '%s\n%s' "$2" "$1" | sort -V -C
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Show usage information
show_usage() {
    cat << EOF
Ansible Development Environment Quick Start

This script sets up a complete development environment for contributing
to Ansible. It performs system checks, installs dependencies, and verifies
the installation.

Usage:
    $0 [OPTIONS]

Options:
    --silent        Run in non-interactive mode (no prompts)
    --no-venv       Skip virtual environment creation
    --skip-tests    Skip installation verification tests
    --help          Show this help message

Examples:
    $0                      # Interactive setup with all checks
    $0 --silent             # Automated setup for CI/CD
    $0 --no-venv            # Setup without creating virtualenv

For more information, see:
    https://docs.ansible.com/ansible/devel/community/
EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --silent)
                SILENT_MODE=true
                shift
                ;;
            --no-venv)
                SKIP_VENV=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                show_usage
                exit 1
                ;;
        esac
    done
}

# Prompt user for yes/no answer (returns 0 for yes, 1 for no)
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-y}"

    if [[ "$SILENT_MODE" == true ]]; then
        return 0
    fi

    local answer
    if [[ "$default" == "y" ]]; then
        read -r -p "$prompt [Y/n]: " answer
        answer="${answer:-y}"
    else
        read -r -p "$prompt [y/N]: " answer
        answer="${answer:-n}"
    fi

    [[ "$answer" =~ ^[Yy] ]]
}

# Step 1: Check system requirements
check_system_requirements() {
    print_step "1/7" "Checking system requirements"

    local all_checks_passed=true

    # Check git
    if command_exists git; then
        local git_version
        git_version=$(git --version | cut -d' ' -f3)
        print_success "Git found (version $git_version)"
    else
        print_error "Git not found"
        print_info "Install git: sudo apt-get install git  # Ubuntu/Debian"
        print_info "             sudo dnf install git      # Fedora/RHEL"
        all_checks_passed=false
    fi

    # Check Python version
    if command_exists python3; then
        local python_version
        python_version=$(python3 --version | cut -d' ' -f2)
        if version_ge "$python_version" "$REQUIRED_PYTHON_VERSION"; then
            print_success "Python found (version $python_version, required >=$REQUIRED_PYTHON_VERSION)"
        else
            print_error "Python version too old (found $python_version, required >=$REQUIRED_PYTHON_VERSION)"
            print_info "See: https://docs.ansible.com/ansible/devel/installation_guide/"
            all_checks_passed=false
        fi
    else
        print_error "Python 3 not found"
        all_checks_passed=false
    fi

    # Check pip
    if python3 -m pip --version &> /dev/null; then
        local pip_version
        pip_version=$(python3 -m pip --version | cut -d' ' -f2)
        print_success "pip found (version $pip_version)"
    else
        print_error "pip not found"
        print_info "Install pip: python3 -m ensurepip --upgrade"
        all_checks_passed=false
    fi

    if [[ "$all_checks_passed" == false ]]; then
        print_error "System requirements not met. Please install missing components."
        exit 1
    fi
}

# Step 2: Handle virtual environment
setup_virtual_environment() {
    print_step "2/7" "Checking virtual environment"

    if [[ "$SKIP_VENV" == true ]]; then
        print_info "Skipping virtual environment setup (--no-venv specified)"
        return 0
    fi

    if [[ -n "$VIRTUAL_ENV" ]]; then
        print_success "Already in virtual environment: $VIRTUAL_ENV"
        return 0
    fi

    print_warning "Not currently in a virtual environment"
    print_info "Using a virtual environment is recommended to avoid conflicts"
    print_info "with system Python packages."

    if prompt_yes_no "Create and activate a virtual environment?"; then
        local venv_path="$ANSIBLE_ROOT/.venv"

        print_info "Creating virtual environment at $venv_path"
        if python3 -m venv "$venv_path"; then
            print_success "Virtual environment created"

            print_info "Activating virtual environment"
            # Note: We can't actually activate it in this script for the parent shell
            # shellcheck disable=SC1091
            source "$venv_path/bin/activate"
            print_success "Virtual environment activated for this session"
            print_warning "To activate in future sessions, run:"
            print_warning "  source $venv_path/bin/activate"
        else
            print_error "Failed to create virtual environment"
            return 1
        fi
    else
        print_info "Continuing without virtual environment"
    fi
}

# Step 3: Setup Ansible development environment
setup_ansible_environment() {
    print_step "3/7" "Setting up Ansible development environment"

    local env_setup_script="$SCRIPT_DIR/env-setup"

    if [[ ! -f "$env_setup_script" ]]; then
        print_error "env-setup script not found at $env_setup_script"
        return 1
    fi

    print_info "Sourcing $env_setup_script"
    # Source the env-setup script in silent mode
    # shellcheck disable=SC1090
    source "$env_setup_script" -q

    print_success "Ansible environment configured"
    print_info "PYTHONPATH includes: ${ANSIBLE_ROOT}/lib"
    print_info "PATH includes: ${ANSIBLE_ROOT}/bin"
}

# Step 4: Install dependencies
install_dependencies() {
    print_step "4/7" "Installing Python dependencies"

    local requirements_file="$ANSIBLE_ROOT/requirements.txt"

    if [[ ! -f "$requirements_file" ]]; then
        print_error "requirements.txt not found at $requirements_file"
        return 1
    fi

    local package_count
    package_count=$(grep -c '^[^#]' "$requirements_file" || true)
    print_info "Installing $package_count required packages"

    if python3 -m pip install -q -r "$requirements_file"; then
        print_success "All dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        print_info "Try manually: pip install -r requirements.txt"
        return 1
    fi
}

# Step 5: Verify installation
verify_installation() {
    if [[ "$SKIP_TESTS" == true ]]; then
        print_step "5/7" "Skipping installation verification (--skip-tests specified)"
        return 0
    fi

    print_step "5/7" "Verifying installation"

    local tests_passed=0
    local tests_total=5

    # Test 1: ansible command exists
    if command_exists ansible; then
        print_success "ansible command found"
        ((tests_passed++))
    else
        print_error "ansible command not found in PATH"
    fi

    # Test 2: ansible version
    if ansible --version &> /dev/null; then
        local version
        version=$(ansible --version 2>/dev/null | head -n1)
        print_success "ansible version check passed: $version"
        ((tests_passed++))
    else
        print_error "ansible --version failed"
    fi

    # Test 3: ansible-config command
    if ansible-config --help &> /dev/null; then
        print_success "ansible-config command working"
        ((tests_passed++))
    else
        print_error "ansible-config command failed"
    fi

    # Test 4: Python imports
    if python3 -c "import ansible; ansible.__version__" &> /dev/null; then
        local py_version
        py_version=$(python3 -c "import ansible; print(ansible.__version__)")
        print_success "Python module imports working (ansible $py_version)"
        ((tests_passed++))
    else
        print_error "Failed to import ansible Python module"
    fi

    # Test 5: Basic ansible command
    if ansible localhost -m ping &> /dev/null; then
        print_success "ansible ping test passed"
        ((tests_passed++))
    else
        print_warning "ansible ping test failed (this is usually not critical)"
        ((tests_passed++))
    fi

    echo ""
    if [[ $tests_passed -eq $tests_total ]]; then
        print_success "All verification tests passed ($tests_passed/$tests_total)"
    else
        print_warning "Some tests failed ($tests_passed/$tests_total passed)"
        print_info "This may not be critical. Try running: ansible --version"
    fi
}

# Step 6: Create convenience activation script
create_activation_script() {
    print_step "6/7" "Creating convenience activation script"

    local activation_script="$ANSIBLE_ROOT/.activate-dev.sh"

    cat > "$activation_script" << 'EOF'
#!/usr/bin/env bash
# Convenience script for activating Ansible development environment
# Usage: source .activate-dev.sh

# Determine script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtualenv if it exists
if [[ -d "$SCRIPT_DIR/.venv" ]]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "Virtual environment activated"
fi

# Setup Ansible environment (silent mode)
if [[ -f "$SCRIPT_DIR/hacking/env-setup" ]]; then
    source "$SCRIPT_DIR/hacking/env-setup" -q
    echo "Ansible development environment ready"
    echo "  Python: $(python3 --version)"
    echo "  Ansible: $(ansible --version 2>/dev/null | head -n1)"
else
    echo "Warning: env-setup script not found"
fi
EOF

    chmod +x "$activation_script"
    print_success "Created $activation_script"
    print_info "In future sessions, run: source .activate-dev.sh"
}

# Step 7: Display next steps
show_next_steps() {
    print_step "7/7" "Setup complete"

    print_success "Your Ansible development environment is ready"

    echo ""
    echo "============================================================"
    echo "  Next Steps"
    echo "============================================================"
    echo ""
    echo "1. Activate the environment in new shell sessions:"
    echo "   $ source .activate-dev.sh"
    echo ""
    echo "2. Verify your setup:"
    echo "   $ ansible --version"
    echo "   $ ansible-config --help"
    echo ""
    echo "3. Explore the codebase:"
    echo "   $ ls lib/ansible/"
    echo "   $ less hacking/README.md"
    echo ""
    echo "4. Run tests to understand how things work:"
    echo "   $ ansible-test --help"
    echo ""
    echo "5. Find good first issues to contribute:"
    echo "   https://github.com/ansible/ansible/labels/good%20first%20issue"
    echo ""
    echo "6. Read the contributor guide:"
    echo "   https://docs.ansible.com/ansible/devel/community/"
    echo ""
    echo "7. Join the community:"
    echo "   https://forum.ansible.com/"
    echo ""
    echo "============================================================"
    echo ""
}

# Main execution flow
main() {
    parse_arguments "$@"

    print_header

    # Change to Ansible root directory
    cd "$ANSIBLE_ROOT" || {
        print_error "Failed to change to Ansible root directory: $ANSIBLE_ROOT"
        exit 1
    }

    # Execute setup steps
    check_system_requirements
    setup_virtual_environment
    setup_ansible_environment
    install_dependencies
    verify_installation
    create_activation_script
    show_next_steps

    echo "Setup script completed successfully."
    echo ""
}

# Run main function
main "$@"

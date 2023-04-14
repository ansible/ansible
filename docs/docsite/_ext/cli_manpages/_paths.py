"""Path constants."""

from pathlib import Path


PROJECT_DIR_PATH = Path(__file__).parents[4]
PROJECT_BIN_DIR_PATH = PROJECT_DIR_PATH / 'bin'
TEMPLATES_DIR_PATH = PROJECT_DIR_PATH / 'docs' / 'templates'
CLI_IMPORTABLES_DIR_PATH = PROJECT_DIR_PATH / 'lib' / 'ansible' / 'cli'

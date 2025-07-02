import pytest
from unittest.mock import patch, MagicMock

class TestTimeCommand:
    def test_adds_timestamps(self):
        
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        
        # stdin returns one line
        mock_stdin.__iter__ = lambda self: iter(["Hello\n"])
        
        with patch('sys.stdin', mock_stdin), \
             patch('sys.stdout', mock_stdout), \
             patch('time.time', side_effect=[0, 65]):
            
            exec(open('.azure-pipelines/scripts/time-command.py').read(), {'__name__': '__main__'})
            
            mock_stdout.write.assert_called_with("01:05 Hello\n")
        
       
// crt_setmode.c
// This program uses _setmode to change
// stdout from text mode to binary mode.
// Used to test output_encoding_override for win_command.

#include <stdio.h>
#include <fcntl.h>
#include <io.h>

int main(void)
{
	_setmode(_fileno(stdout), _O_BINARY);
	// Translates to 日本 in shift_jis
	printf("\x93\xFa\x96\x7B - Japan");
}

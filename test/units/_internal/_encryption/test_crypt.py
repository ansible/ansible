from __future__ import annotations

import errno
import pytest
from pytest_mock import MockerFixture

from ansible._internal._encryption._crypt import _CryptLib, CryptFacade, _FAILURE_TOKENS


class TestCryptFacade:

    def test_unsupported_platform(self, mocker: MockerFixture) -> None:
        """Test that unsupported platforms are skipped."""
        mock_libs = (
            _CryptLib('foo', include_platforms=frozenset({'fake_platform'})),
        )
        mocker.patch('ansible._internal._encryption._crypt._CRYPT_LIBS', mock_libs)

        with pytest.raises(ImportError, match=r'Cannot find crypt implementation'):
            CryptFacade()

    def test_libc_fallback(self, mocker: MockerFixture) -> None:
        """Test that a library name of None will load the libc library."""
        mock_libs = (
            _CryptLib(None),
        )
        mocker.patch('ansible._internal._encryption._crypt._CRYPT_LIBS', mock_libs)
        load_lib_mock = mocker.patch('ctypes.cdll.LoadLibrary')

        crypt_facade = CryptFacade()

        load_lib_mock.assert_called_once_with(None)
        assert crypt_facade._crypt_name is None

    def test_library_with_no_crypt_methods(self, mocker: MockerFixture) -> None:
        """Test that a library without crypt() and crypt_r() is skipped."""
        mock_libs = (
            _CryptLib(None),
        )

        class MockCDLL:
            pass

        mocker.patch('ansible._internal._encryption._crypt._CRYPT_LIBS', mock_libs)
        mocker.patch('ctypes.cdll.LoadLibrary', return_value=MockCDLL())

        with pytest.raises(ImportError, match=r'Cannot find crypt implementation'):
            CryptFacade()

    def test_library_with_no_crypt_r_or_crypt_gensalt_rn(self, mocker: MockerFixture) -> None:
        """Test that a library without crypt_r() or crypt_gensalt_rn() is prepped correctly."""
        mock_libs = (
            _CryptLib(None),
        )

        class MockCDLL:

            class MockCrypt:
                def __init__(self):
                    self.argtypes = None
                    self.restype = None

            def __init__(self):
                self.crypt = self.MockCrypt()
                self.crypt_gensalt = self.MockCrypt()

        mocker.patch('ansible._internal._encryption._crypt._CRYPT_LIBS', mock_libs)
        mocker.patch('ctypes.cdll.LoadLibrary', return_value=MockCDLL())

        crypt_facade = CryptFacade()

        assert crypt_facade._crypt_impl is not None
        assert crypt_facade._crypt_impl.argtypes is not None
        assert crypt_facade._crypt_impl.restype is not None
        assert crypt_facade._use_crypt_r is False

        assert crypt_facade._crypt_gensalt_impl is not None
        assert crypt_facade._crypt_gensalt_impl.argtypes is not None
        assert crypt_facade._crypt_gensalt_impl.restype is not None
        assert crypt_facade._use_crypt_gensalt_rn is False
        assert crypt_facade.has_crypt_gensalt

    def test_crypt_fail_errno(self, mocker: MockerFixture) -> None:
        """Test crypt() setting failure errno raises OSError."""
        mocker.patch('ctypes.get_errno', return_value=errno.EBADFD)
        crypt_facade = CryptFacade()

        with pytest.raises(OSError, match=r'crypt failed:'):
            crypt_facade.crypt(b"test", b"123")

    def test_crypt_result_none(self, mocker: MockerFixture) -> None:
        """Test crypt() implementation returning None raises ValueError."""
        crypt_facade = CryptFacade()
        mocker.patch.object(crypt_facade, '_crypt_impl', return_value=None)

        with pytest.raises(ValueError, match=r'crypt failed: invalid salt or unsupported algorithm'):
            crypt_facade.crypt(b"test", b"123")

    def test_crypt_result_failure(self, mocker: MockerFixture) -> None:
        """Test crypt() implementation returning failure token raises ValueError."""
        crypt_facade = CryptFacade()
        mocker.patch.object(crypt_facade, '_crypt_impl', return_value=list(_FAILURE_TOKENS)[0])

        with pytest.raises(ValueError, match=r'crypt failed: invalid salt or unsupported algorithm'):
            crypt_facade.crypt(b"test", b"123")

    def test_crypt_gensalt_called_with_no_impl(self, mocker: MockerFixture) -> None:
        """Calling crypt_gensalt() without impl should raise NotImplementedError."""
        crypt_facade = CryptFacade()
        mock_prop = mocker.patch('ansible._internal._encryption._crypt.CryptFacade.has_crypt_gensalt', new_callable=mocker.PropertyMock)
        mock_prop.return_value = False

        with pytest.raises(NotImplementedError, match=r'crypt_gensalt not available \(requires libxcrypt\)'):
            crypt_facade.crypt_gensalt(b"", 1, b"")

    def test_crypt_gensalt(self, mocker: MockerFixture) -> None:
        """Test the NOT _use_crypt_gensalt_rn code path of crypt_gensalt()."""
        crypt_facade = CryptFacade()
        crypt_facade._use_crypt_gensalt_rn = False
        mock_impl = mocker.patch.object(crypt_facade, '_crypt_gensalt_impl', return_value='')

        crypt_facade.crypt_gensalt(b'', 1, b'')
        mock_impl.assert_called_once_with(b'', 1, b'', 0)

    def test_crypt_gensalt_fail_errno(self, mocker: MockerFixture) -> None:
        """Test crypt_gensalt() setting failure errno raises OSError."""
        mocker.patch('ctypes.get_errno', return_value=errno.EBADFD)
        crypt_facade = CryptFacade()

        with pytest.raises(OSError, match=r'crypt_gensalt failed:'):
            crypt_facade.crypt_gensalt(b'', 1, b'')

    def test_crypt_gensalt_result_none(self, mocker: MockerFixture) -> None:
        """Test crypt_gensalt() implementation returning None raises ValueError."""
        crypt_facade = CryptFacade()
        mocker.patch.object(crypt_facade, '_crypt_gensalt_impl', return_value=None)

        with pytest.raises(ValueError, match=r'crypt_gensalt failed: unable to generate salt'):
            crypt_facade.crypt_gensalt(b'', 1, b'')

    def test_crypt_gensalt_result_failure(self, mocker: MockerFixture) -> None:
        """Test crypt_gensalt() implementation returning failure token raises ValueError."""
        crypt_facade = CryptFacade()
        # Skip the _rn version as it modifies impl return value
        crypt_facade._use_crypt_gensalt_rn = False
        mocker.patch.object(crypt_facade, '_crypt_gensalt_impl', return_value=list(_FAILURE_TOKENS)[0])

        with pytest.raises(ValueError, match=r'crypt_gensalt failed: invalid prefix or unsupported algorithm'):
            crypt_facade.crypt_gensalt(b'', 1, b'')

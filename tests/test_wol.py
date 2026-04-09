from unittest.mock import patch
from wolnut.wol import send_wol_packet


def test_send_wol_packet_success():
    with patch("wolnut.wol.send_magic_packet") as mock:
        assert send_wol_packet("aa:bb:cc:dd:ee:ff") is True
        mock.assert_called_once_with("aa:bb:cc:dd:ee:ff", ip_address="255.255.255.255")


def test_send_wol_packet_failure():
    with patch("wolnut.wol.send_magic_packet", side_effect=Exception("fail")):
        assert send_wol_packet("aa:bb:cc:dd:ee:ff") is False

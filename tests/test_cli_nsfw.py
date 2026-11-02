"""The CLI passes --nsfw / --no-nsfw through to create and update; omitting both sends nothing."""

from unittest.mock import patch

import pytest

from jargon import __main__ as cli


def _run(argv):
    sent = {}

    def fake_request(args, message):
        sent.update(message)
        return {"term": {"slug": message.get("slug", "x")}}

    with patch("jargon.client.request", side_effect=fake_request):
        code = cli.main(argv)
    return code, sent


@pytest.mark.unit
def test_create_with_nsfw_sends_true():
    code, sent = _run(["--create", "--slug", "x", "--term", "X", "--definition", "d", "--nsfw"])
    assert code == 0 and sent["nsfw"] is True


@pytest.mark.unit
def test_create_with_no_nsfw_sends_false():
    code, sent = _run(["--create", "--slug", "x", "--term", "X", "--definition", "d", "--no-nsfw"])
    assert code == 0 and sent["nsfw"] is False


@pytest.mark.unit
def test_create_without_flag_sends_no_nsfw_so_the_default_applies():
    code, sent = _run(["--create", "--slug", "x", "--term", "X", "--definition", "d"])
    assert code == 0 and "nsfw" not in sent


@pytest.mark.unit
def test_update_nsfw_only_is_accepted_and_sent():
    code, sent = _run(["--update", "--slug", "x", "--no-nsfw"])
    assert code == 0 and sent == {"type": "jargon_update", "slug": "x", "nsfw": False}


@pytest.mark.unit
def test_nsfw_and_no_nsfw_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        cli.buildparser().parse_args(["--create", "--nsfw", "--no-nsfw"])

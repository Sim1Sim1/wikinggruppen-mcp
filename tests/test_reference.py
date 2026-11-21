import pytest

from wikinggruppen_mcp import reference as ref
from wikinggruppen_mcp.client import WgrError, check_read, check_write


def test_all_classes_have_methods():
    names = {m["method"].split(".")[0] for m in ref.list_methods()}
    assert {"Article", "Category", "Stock", "Order", "ProductImage"} <= names


def test_article_set_has_h1_and_title():
    fields = {p["name"] for p in ref.describe("Article.set")["request_params"]}
    assert {"h1_{languageCode}", "title_{languageCode}", "id", "articleNumber"} <= fields


def test_unknown_method_suggests():
    with pytest.raises(KeyError, match="Article.get"):
        ref.describe("article.g")


def test_find_field():
    assert any(h["method"] == "Article.get" for h in ref.find_field("getURLs"))


def test_workflow_section():
    assert "h1_sv" in ref.workflow_section("product text")
    assert "No workflow" in ref.workflow_section("nonsense")


def test_read_guard():
    check_read("Article.get")
    with pytest.raises(WgrError):
        check_read("Article.set")


def test_write_guard(monkeypatch):
    monkeypatch.delenv("WGR_ALLOW_WRITE", raising=False)
    with pytest.raises(WgrError, match="off"):
        check_write("Article.set")
    monkeypatch.setenv("WGR_ALLOW_WRITE", "1")
    check_write("Article.set")
    for bad in ("Order.cancel", "NewsletterRecipient.delete", "PriceList.delete", "OrderStatus.delete", "ProductImage.delete"):
        with pytest.raises(WgrError):
            check_write(bad)

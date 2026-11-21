# Wikinggruppen API: things the docs do not tell you

Learned by using the API against a live shop (Nov 2026, docs version 8.4.0; 11.0.0 differs only by `isInNavigation` on Category). Each point says how sure we are.

## Requests and answers

- **JSON-RPC ids start at 1.** A command with `id: 0` is answered without an id, so the answer cannot be matched. Number commands 1..n.
- **Check every command's own result.** One request can carry many commands (20 per request worked well). A failed command does not stop the others, so some may already be written when another fails.
- **The success value differs per method.** `Article.set` and `Article.create` return an object `{articleNumber, id, productId}`. `Category.set` returns `true`, `Category.create` the new id. Do not test an `Article.set` answer against `true`: that made a successful write look like a failure.
- **`Article.get` always returns an array**, also for one article. Filter on `articleNumber` in the result.
- **Basic Auth.** The user name is given by Wikinggruppen without brackets. Each shop has its own copy of the API, so a method or field can exist in one shop and not another. Ask Wikinggruppen when something is missing.
- **Shops behind Cloudflare.** A shop whose domain is proxied by Cloudflare answers `403 error code: 1106` to calls from a Cloudflare Worker. The same call works from a normal machine. The forwarding service (`https://api.wikinggruppen.se/forward/` with the shop's URL in the header `Api-Url`) works from a normal machine, but from a Worker it answered `400 Header Api-Url is missing`. Not solved. Run API jobs from a laptop, a server or CI, not from a Worker, until Wikinggruppen allows the caller or fixes the forwarding.

## URLs and titles

- **A title change moves the page.** Article URLs follow `title_*`, category and front. Category URLs follow title and parent. Wikinggruppen then sets up a 301 from the old URL by itself (confirmed by the shop owner, redirect not tested by us).
- **To change the visible heading without moving the page, write `h1_*` and leave `title_*` alone.** The docs say `h1_*` is "the value of the H1 tag if it should be different from the product title". Setting `h1_sv` to the new title and putting the old title back restored the original URL. Not checked: that every theme prints `h1_*` as the page heading.
- `Article.get` with `getURLs: true` returns the URL per language and front. Use it to check that a write did not move a page.

## Data model

- **Two levels of article.** `id` is the variant (what an article number points to), `productId` the product. Fields marked `*` in the docs are product-level and shared by all variants. Variants share `externalParentArticleNumber`.
- **Article numbers are unique.** If a new number is not unique the API changes it, so read the answer, do not assume.
- **Hidden articles are many.** A shop can hold more hidden than visible articles (old ranges, supplier lines). `isHidden` is the only way to take an article out: there is no article delete. Categories cannot be deleted either (set `isVisible: false`).
- **Category paths.** `path_sv` joins names with " - ", which also occurs inside names ("Sauna - Accessories"). Build paths from the `parentId` chain if you need something unambiguous. Category ids are fixed through renames and moves, so match on id.
- **Descriptions can carry markup from the theme.** A shop's `description_sv` may contain tab containers, a specification table and a data-sheet link inside the description. `Article.set` replaces the whole value, so those parts are lost when you write a new description. Look at a sample first.

## What the API cannot do (compared with the import file)

No specification table, no unit (`Enhet`), no product documents, no list price, no delivery time / back-order dates, no energy class, no main category, no article delete, no category delete. Those fields exist only in the CSV/Excel import. Images: `ProductImage.create` takes base64 plus `productId`, not a URL, and `ProductImage.delete` with only `productId` removes all images of the product.

## Reading a lot of data

- `Article.get` without parameters returns everything. For a large shop that is far too big for one call. Read per category (`categoryId`) in a loop and drop duplicates on `id`. An article that is in no category is not found this way.
- For updates, use `updatedFrom` (`YYYY-MM-DD HH:MM:SS`) on `Article.get`, `Stock.get` and `Order.get`.
- A full read of about 57 000 articles took about 5 minutes and gave about 100 MB of JSON.

## Writing safely

The terms of use say the API is used at your own risk and restoring from Wikinggruppen's backup is slow and may cost money. So:
1. Take your own backup before any bulk write: all categories and all articles (see `workflows.md`).
2. Read each article fresh and write only the fields that differ.
3. Do not send empty strings for fields you do not mean to clear. Send only fields that are set.
4. Log old and new values for every write.
5. Start with one article, look at it in the shop, then run the batch.

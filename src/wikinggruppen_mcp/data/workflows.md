# Workflows

Each one is a recipe in order. Tools: `wgr_describe_method` for the parameters, `wgr_read` to look, `wgr_write` to change (only with `WGR_ALLOW_WRITE=1`).

## Backup before a bulk write
1. `Category.get` with no parameters: all categories.
2. `Article.get` per category id (`{"categoryId": id, "getURLs": true, "getImages": true}`), 20 commands per request. Remove duplicates on `id`.
3. Save both as files outside the repo. Restore is `Article.set` / `Category.set` with the saved values for the fields you want back, matched on `id`. Compare with the live shop first and print the plan before writing.

## Update product text (title, description, meta)
1. `Article.get {"articleNumber": N, "getURLs": true}`, take the matching element.
2. Compare each field you want to write with the live value. Skip those that are equal.
3. If the text was written by you earlier and the live value now differs from what you wrote, someone edited it in the shop. Stop and ask.
4. `Article.set {"id": live.id, ...changed fields}`. Fields: `description_sv`, `metaTitle_sv`, `metaDescription_sv`, `h1_sv`. **New heading goes to `h1_sv`, never `title_sv`** unless the URL is meant to change.
5. Check the answer is an object with the same `id`. Save what you wrote so step 3 works next time. Keep the old values in a log.

## Update prices
`price_SEK`, `inPrice` (ex VAT) and `campaignPrice_SEK` (with `campaignActive`, `campaignDateStart`, `campaignDateEnd`) are set with `Article.set`. Many articles in one request: one `Article.set` command per article. Prices are per currency code. Staggered and price-list prices are arrays (`staggeringPrices`, `priceListPrices`) that replace the old arrays.

## Update stock
`Stock.set` takes an array in `params`, each row `{articleNumber, stock, stockType, isBackOrder}`. `Stock.get {"updatedFrom": "..."}` returns only changed rows. `stockType` 1 = infinite, 2 = limited. `isBackOrder` is product-level.

## Create articles
`Article.create` needs `categoryId` and `articleNumber`, otherwise as `Article.set`. Variants: the same `externalParentArticleNumber` on every variant and the same option titles (`options[].title_sv`, `options[].value_sv`). Set `weight` (shipping may depend on it; a shop can give free shipping when it is missing). Hide new articles (`isHidden: true`) until text, image and price are ready. Images afterwards with `ProductImage.create` (base64).

## Change the category tree
`Category.create` returns the new id; create parents first, give `frontId` (the shop's front ids come from `Front.get`) and keep new categories hidden until they have content. `Category.set` with `title` or `parentId` moves the URLs of the category and all its articles (301 follows). Match on id. A category cannot be deleted: hide it.

## The import file (not the API)
Wikinggruppen's admin has one import for everything. It needs `Article number`, first row is headings, it recognises its own headings and lets you pick which columns to read (for example only price). Headings: `Article number`, `Name`, `Description`, `Specification (sv)`, `EAN`, `Enhet`, `Image 1`..`Image 5`, `Inprice excl. VAT`, `Price incl. VAT`, `Price excl. VAT`, `VAT`, `Listpris`, `Producer`, `Model`, `Product document`, `Category`, `Sub category`, `Weight (g)`, `Meta title`, `Meta description`, `Campaign price incl. VAT` with `Campaign start date` / `end date`, `Stock`, `InfStock 1/0`, `Backorder (1/0)` with `backOrderStart` / `backOrderEnd` / `backOrderUnit sv`, `Empty stock text`, `Hidden 1/0`, `Ignore 1/0`, `Energy class`. Use the import for what the API cannot do (specification table, delivery time, unit, documents). Category depth in the import may be limited to two levels: check with Wikinggruppen.

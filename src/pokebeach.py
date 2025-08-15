from seleniumbase import Driver


def get_newsfeed() -> list[str]:
    posts = []
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode("https://www.pokebeach.com/")
    sb.sleep(1)
    post_div = sb.cdp.find_visible_elements("div.xpress_articleList")[0]
    for post in post_div.children:
        a_element = post
        empty_post = False
        for _ in range(6):
            if len(a_element.children) == 0:
                empty_post = True
                break
            a_element = a_element.children[0]

        if empty_post:
            continue

        post_url = a_element["href"]
        posts.append(post_url)

    sb.quit()
    return posts

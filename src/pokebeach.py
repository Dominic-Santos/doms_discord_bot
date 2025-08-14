from seleniumbase import Driver


def get_newsfeed() -> list[str]:
    posts = []
    sb = Driver(uc=True, locale_code="en", ad_block=True)
    sb.uc_activate_cdp_mode("https://www.pokebeach.com/")
    sb.sleep(1)
    post_div = sb.cdp.find_visible_elements("div.xpress_articleList")[0]
    for post in post_div.children:
        try:
            a_element = post
            for _ in range(6):
                a_element = a_element.children[0]
            post_url = a_element["href"]
            posts.append(post_url)
        except Exception as e:
            print(e)
            pass
    sb.quit()
    return posts

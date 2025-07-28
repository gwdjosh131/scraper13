"""
Facebook Scraper CSS Class Constants

This file maintains the CSS class names used for scraping Facebook content.
Facebook frequently changes these class names, so they may need periodic updates.

The constants are organized by functionality:
- Post container classes
- User information classes
- Post text content classes for different formats
- Comment-related classes
- Button and UI element classes

These CSS selectors are used by the scraper to locate and extract content from Facebook's DOM.
"""

# Post container and main structure classes
post_class = "x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z" # within the feed div, there exist posts: these are the post classes - in order
post_class_obj = {
    "css_selector": "", "xpath": "//div[@role='feed']/div[.//div[@aria-posinset]]"
}

# Post author section related classes
poster_info_class = "html-div xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x1iyjqo2 xeuugli"  # the container of the username and the date
poster_info_class_obj = { # TODO not finished, replaced by xpath of date_enclosing_span_obj
    'css_selector': ".html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1iyjqo2.xeuugli", "xpath": ""
}

poster_username_strong = "html-strong xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs x1s688f"  # the strong tag which contains a span containing the username

date_enclosing_span = "xmper1u xt0psk2 xjb2p0i x1qlqyl8 x15bjb6t x1n2onr6 x17ihmo5 x1g77sc7"  # the span which encloses the date (the date whcih needs to be hovered over)
date_enclosing_span_obj = { # NOT IN THE POPUP
    "css_selector": "", "xpath": "//div[@data-ad-rendering-role='profile_name']/ancestor::div[1]/following-sibling::div//a[@target='_blank']"
}

# dialog pop-up window class
pop_up_whole_window_class="x1n2onr6 x1ja2u2z x1afcbsf xdt5ytf x1a2a7pz x71s49j x1qjc9v5 xrjkcco x58fqnu x1mh14rs xfkwgsy x78zum5 x1plvlek xryxfnj xcatxm7 xrgej4m xh8yej3" # the dialog pop-up, sorta like a full screen of the post
pop_up_whole_window_class_obj = {
    "xpath": "//div[@role='dialog']//div[./hr]/.."
}

comment_pop_up_class="html-div x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1gslohp" # this is the section which wraps all the comments in the dialog pop-up
comment_pop_up_class_obj = {
    "xpath": "(//div[@role='dialog']//div[./hr]/..//div[.//div[@aria-label='Leave a comment']]/following-sibling::div[1]/div[last()])[2]"
}

comment_loader_class="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x78zum5 x13a6bvl" # this class's element (div) contains information about loading comments
comment_loader_class_obj = {
    "xpath": "(.//div[@role='status' and @aria-label='Loading...'])[last()]"
}

# pop-up-comment's info
individual_comment_class="xwib8y2 xn6708d x1ye3gou x1y1aw1k"
individual_comment_class_obj = {
    "xpath": ".//div[@role='article']"
}

individual_comment_name_class="x6zurak x18bv5gf x184q3qc xqxll94 x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x193iq5w xeuugli x13faqbe x1vvkbs x1lliihq xzsf02u xlh3980 xvmahel x1x9mg3 x1s688f"
individual_comment_name_obj = {
    "xpath": ".//a[@aria-hidden='false'][1]//span[@dir='auto']"
}

individual_comment_text_class="xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs"
individual_comment_text_obj = {
    "xpath": ".//div[@dir='auto' and not(ancestor::a)]"
}

interior_popup_section_class="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x78zum5 xdt5ytf x1iyjqo2 x7ywyr2" # This class is useful for the scrape_for_post_info function


# popup post text classes
post_text_obj = {
    "xpath": "//div[@role='dialog']//div[./hr]/..//div[@data-ad-rendering-role='story_message']"
}

username_popup_obj = {
    "xpath": """//div[@role='dialog']//div[./hr]/..//h2[contains(., "'s post")]"""
}

date_popup_obj = {
    "xpath": """(//div[@role='dialog']//div[.//div[@data-ad-rendering-role='profile_name']]/following-sibling::div//span[./a[@attributionsrc]])[2]"""
}

# popup other info classes
pop_up_username_class="x6zurak x18bv5gf x193iq5w xeuugli x13faqbe x1vvkbs xt0psk2 xi81zsa xlh3980 xvmahel x1x9mg3 x1s688f"
pop_up_usernames_post_class="html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd xh8yej3" # this class represents the 'header' of a post which say's (username)'s post
pop_up_date_section="html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"
js_date_class = "x6zurak x18bv5gf x193iq5w xeuugli x13faqbe x1vvkbs xt0psk2 xzsf02u xlh3980 xvmahel x1x9mg3 xo1l8bm"  # the class for the rendered js date


pop_up_reel_class="x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1rg5ohu x1a2a7pz x1n2onr6 xh8yej3" # this is the class for reposted reel content.
pop_up_repost_class="x1i10hfl x1qjc9v5 xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1q0g3np x87ps6o x1lku1pv x1a2a7pz x1lliihq x1pdlv7q" # this class is for a non-reel image repost

# Captcha Classes
captcha_input_class = "x1i10hfl xggy1nq xtpw4lu x1tutvks x1s3xk63 x1s07b3s x1kdt53j x1a2a7pz xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 xzsf02u x1uxerd5 x1fcty0u x132q4wb x1a8lsjc x1pi30zi x1swvt13 x9desvi xh8yej3"
captcha_login_class = "x1ja2u2z x78zum5 x2lah0s x1n2onr6 xl56j7k x6s0dn4 xozqiw3 x1q0g3np x972fbf xcfux6l x1qhh985 xm0m39n x9f619 xtvsq51 xqdzp0n x15p4eik x1ismhnl x16ie3sq x1xila8y x1xarc30 xrwyoh0"


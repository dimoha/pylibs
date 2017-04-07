from pylibs.network.browser import Browser
from pylibs.network.urls import url_from_pynicode, get_host

def check_mirror(domain):

    br = Browser()

    all_effective_hosts = set()
    for url in [domain, 'www.%s' % domain]:
        br.get(url)
        eff_url = url_from_pynicode(br.effective_url)
        host = get_host(eff_url)
        all_effective_hosts.add(host)

    if len(set(all_effective_hosts))==2:
        main_mirror = 'both'
    else:
        main_mirror = 'with_www' if list(all_effective_hosts)[0].startswith('www.') else 'without_www'

    return main_mirror
'''Live evidence gathering: web search and website checks for OpportunityGuard AI.'''

from datetime import datetime, timezone
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
}

SEARCH_ENDPOINT = 'https://html.duckduckgo.com/html/?q='


def _clean_result_url(href):
    if href.startswith('//'):
        href = 'https:' + href
    if 'uddg=' in href:
        targets = parse_qs(urlparse(href).query).get('uddg')
        if targets:
            return unquote(targets[0])
    return href


def search_web(query, max_results=5):
    '''Search the web via the DuckDuckGo HTML endpoint. Returns [] on any failure.'''
    try:
        response = requests.get(SEARCH_ENDPOINT + quote(query), headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for block in soup.select('div.result'):
        link = block.select_one('a.result__a')
        if not link or not link.get('href'):
            continue
        snippet_el = block.select_one('.result__snippet')
        results.append({
            'title': link.get_text(' ', strip=True),
            'url': _clean_result_url(str(link.get('href'))),
            'snippet': snippet_el.get_text(' ', strip=True) if snippet_el else '',
        })
        if len(results) >= max_results:
            break
    return results


def check_website(url):
    '''Fetch a URL mentioned in the offer and return basic reachability facts.'''
    if not url.startswith('http'):
        url = 'https://' + url
    info = {'url': url, 'reachable': False, 'status_code': None, 'page_title': ''}
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        info['reachable'] = True
        info['status_code'] = response.status_code
        soup = BeautifulSoup(response.text[:200000], 'html.parser')
        title_el = soup.find('title')
        if title_el:
            info['page_title'] = title_el.get_text(' ', strip=True)[:200]
    except requests.RequestException as exc:
        info['error'] = type(exc).__name__
    return info


def gather_evidence(company, urls):
    '''Collect search results and URL checks for the investigation report.'''
    evidence = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'company': company,
        'company_scam_search': [],
        'company_presence_search': [],
        'url_checks': [],
    }
    if company:
        evidence['company_scam_search'] = search_web(
            '"' + company + '" job offer scam OR fraud OR fake complaints', max_results=5
        )
        evidence['company_presence_search'] = search_web(
            '"' + company + '" official site careers India', max_results=5
        )
    for url in urls:
        evidence['url_checks'].append(check_website(url))
    return evidence

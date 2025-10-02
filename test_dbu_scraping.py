"""Quick test to explore DBU match data structure."""

import requests
from bs4 import BeautifulSoup

def test_dbu_scraping():
    """Test what we can scrape from DBU website."""
    
    base_url = 'https://www.dbu.dk/resultater/hold/460174_472317'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    print("🔍 Testing DBU website scraping...")
    print(f"Base URL: {base_url}")
    
    try:
        response = requests.get(base_url, headers=headers)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for navigation links
            print("\n📋 Found navigation links:")
            links = soup.find_all('a', href=True)
            match_related = []
            
            for link in links:
                text = link.get_text(strip=True).lower()
                href = link['href']
                
                if any(keyword in text for keyword in ['kamp', 'resultat', 'program', 'historie', 'match']):
                    full_url = f"https://www.dbu.dk{href}" if href.startswith('/') else href
                    match_related.append({
                        'text': text,
                        'url': full_url
                    })
            
            for item in match_related[:10]:  # Show first 10
                print(f"- {item['text']}: {item['url']}")
            
            # Look for tables
            print(f"\n📊 Found {len(soup.find_all('table'))} tables on main page")
            
            # Try specific match URLs
            test_urls = [
                '/kampe',
                '/kampprogram', 
                '/resultater',
                '/kampprogramresultater'
            ]
            
            print("\n🔗 Testing specific match URLs:")
            for endpoint in test_urls:
                test_url = base_url + endpoint
                try:
                    test_response = requests.get(test_url, headers=headers)
                    print(f"{endpoint}: {test_response.status_code}")
                    
                    if test_response.status_code == 200:
                        test_soup = BeautifulSoup(test_response.text, 'html.parser')
                        tables = test_soup.find_all('table')
                        print(f"  └─ Found {len(tables)} tables")
                        
                        # Look for match-like content
                        for i, table in enumerate(tables[:2]):  # Check first 2 tables
                            rows = table.find_all('tr')
                            if len(rows) > 0:
                                first_row_text = rows[0].get_text(strip=True)[:100]
                                print(f"  └─ Table {i+1} first row: {first_row_text}...")
                
                except Exception as e:
                    print(f"{endpoint}: Error - {e}")
        
        else:
            print(f"❌ Failed to access main page: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_dbu_scraping()
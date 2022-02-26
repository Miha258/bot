import lyricsgenius
import aiohttp
import bs4
import requests
import asyncio

class LyricNotFound(Exception): pass


data = {
        "code": "200",
        "client_secret":'VPo_1Aw7JX-yZB6eiKYyzPUqZibCXLBbewNb1VELwDmZOk1Hm4eSiTV9F9dHnNETbAXVAh4gFZuW5-Ddord3qQ',
        "grant_type": "client_credentials",
        "client_id": "FxkEnVHpw2yc_GJTXWPMl9ZwlfSHzyPMw0Tbxl196hIrY6NsCcod4VQDmuwBvla2",
        "redirect_uri": 'https://www.google.com',
        "response_type": 'code'
}


class GeniusLyric(lyricsgenius.Genius):
    async def get_token(self):
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.genius.com/oauth/token',data=data) as response:
                return await response.json()
    
    
    async def get_lyric(self,track_name):
        genius = lyricsgenius.API(dict(await self.get_token())['access_token'])
        song = genius.search_songs(track_name)
        if len(song['hits']) == 0:
            raise LyricNotFound
        else:
            web_page = song['hits'][0]['result']['url']
            url = genius.web_page(web_page)['web_page']['share_url']
        return url                                
    




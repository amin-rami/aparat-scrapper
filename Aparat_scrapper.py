import asyncio
import aiohttp
import aiofiles
import requests
from constants import *


class AparatScrapper:

    page_API_endpoint = 'https://www.aparat.com/api/fa/v1/user/video/list/username/'
    video_API_endpoint = 'https://www.aparat.com/api/fa/v1/video/video/show/videohash/'
    retrieve_config = '/page/1/perpage/40'


    def __init__(self, username, quality = QAUL_144p):
        self.video_queue = asyncio.Queue()
        self.session = None
        self.scrapped_num = 0
        self.downloading_num = 0
        self.username = username
        self.quality = quality


    async def initial(self):
        url = AparatScrapper.page_API_endpoint + self.username + AparatScrapper.retrieve_config
        self.session = aiohttp.ClientSession()
        while url is not None:
            async with self.session.get(url) as response:
                page_response = await response.json()
                url = None if page_response['data'][0]['attributes']['link'] is None else page_response['data'][0]['attributes']['link']['next']
                videos = page_response['included']
                

                for video in videos:
                    if video['type'] == 'Video':
                        uid = video['attributes']['uid']
                        asyncio.create_task(self.url_getter(uid))
            
        
    async def url_getter(self, uid):
        async with self.session.get(AparatScrapper.video_API_endpoint + uid) as response:
            response = await response.json()
            links = response['data']['attributes']['file_link_all']
            link = links[self.quality]['urls'][0]
            await self.video_queue.put(link)
            self.scrapped_num += 1
            print(f'{self.scrapped_num} videos have been captured')
            print('-'*30)


    async def download_video(self):
        while not self.video_queue.empty():
            try:
                video_url = await self.video_queue.get()
                self.downloading_num += 1
                async with self.session.get(video_url) as response:
                    if response.status == 200:
                        print(f'Downloading video number {self.downloading_num}')
                        print('-'*30)
                        file = await aiofiles.open(f'Videos/video{self.downloading_num}.mp4', mode='wb')
                        await file.write(await response.read())
                        await file.close()

                    else:
                        print(f'Download video {self.downloading_num} failed with status code {response.status}')
                        print('-'*30)
            except Exception as e:
                print('Download video {self.downloading_num} failed')
                print(e)
                print('-'*30)
    

    async def wrapper(self):
        
        await asyncio.gather(self.initial(), self.download_video())

if __name__ == '__main__':
    username = 'itresan'
    aparat_scrapper = AparatScrapper(username, QAUL_144p)

    asyncio.run(aparat_scrapper.wrapper())


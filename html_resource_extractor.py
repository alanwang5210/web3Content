import json
import os
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def _extract_images(soup, resources, base_url):
    """提取图片资源"""
    # 提取<img>标签
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            full_url = urljoin(base_url, src)
            alt_text = img.get('alt', '')
            resources['image'].append({
                'url': full_url,
                'alt': alt_text,
                'type': 'img'
            })

    # 提取CSS背景图片
    for tag in soup.find_all(style=True):
        style = tag.get('style', '')
        urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
        for url in urls:
            if url and not url.startswith('data:'):
                full_url = urljoin(base_url, url)
                resources['image'].append({
                    'url': full_url,
                    'alt': '',
                    'type': 'background-image'
                })


def _extract_videos(soup, resources, base_url):
    """提取视频资源"""
    # 提取<video>标签
    for video in soup.find_all('video'):
        src = video.get('src')
        poster = video.get('poster')

        if src:
            full_url = urljoin(base_url, src)
            resources['video'].append({
                'url': full_url,
                'type': 'video'
            })

        if poster:
            full_poster_url = urljoin(base_url, poster)
            resources['image'].append({
                'url': full_poster_url,
                'alt': 'video poster',
                'type': 'poster'
            })

        for source in video.find_all('source'):
            src = source.get('src')
            if src:
                full_url = urljoin(base_url, src)
                resources['video'].append({
                    'url': full_url,
                    'type': 'video-source',
                    'format': source.get('type', '')
                })

    # 提取<iframe>中的视频
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if src and any(platform in src for platform in
                       ['youtube.com', 'vimeo.com', 'dailymotion.com', 'youku.com', 'bilibili.com']):
            resources['videos'].append({
                'url': src,
                'type': 'iframe-video'
            })


def _extract_audios(soup, resources, base_url):
    """提取音频资源"""
    # 提取<audio>标签
    for audio in soup.find_all('audio'):
        src = audio.get('src')

        if src:
            full_url = urljoin(base_url, src)
            resources['audio'].append({
                'url': full_url,
                'type': 'audio'
            })

        for source in audio.find_all('source'):
            src = source.get('src')
            if src:
                full_url = urljoin(base_url, src)
                resources['audio'].append({
                    'url': full_url,
                    'type': 'audio-source',
                    'format': source.get('type', '')
                })


def print_summary(resources):
    """打印资源摘要"""
    print("\n资源提取摘要:")
    print(f"图片: {len(resources['image'])}")
    print(f"视频: {len(resources['video'])}")
    print(f"音频: {len(resources['audio'])}")
    print(f"文档: {len(resources['file'])}")
    print(f"其他资源: {len(resources['other_resource'])}")
    print(f"总计: {sum(len(v) for v in resources.values())}")


def save_resources(resources, output_file):
    """将资源保存到文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resources, f, ensure_ascii=False, indent=2)
        print(f"资源已保存到: {output_file}")
        return True
    except Exception as e:
        print(f"保存资源失败: {e}")
        return False


class HTMLResourceExtractor:
    """HTML资源提取器，用于提取HTML页面中的图片、视频、音频、文档等资源"""

    def __init__(self):
        """初始化资源提取器"""
        # 定义文档类型的文件扩展名
        self.document_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.csv', '.rtf', '.odt', '.ods', '.odp', '.zip', '.rar'
        ]

    def extract_resources(self, html_content, base_url=''):
        """从HTML内容中提取资源"""
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, 'html.parser')
        resources = {
            'image': [],
            'video': [],
            'audio': [],
            'file': [],
            'other_resource': []
        }

        # 提取图片资源
        _extract_images(soup, resources, base_url)

        # 提取视频资源
        _extract_videos(soup, resources, base_url)

        # 提取音频资源
        _extract_audios(soup, resources, base_url)

        # 提取文档和其他资源
        self._extract_links(soup, resources, base_url)

        return resources

    def _extract_links(self, soup, resources, base_url):
        """提取链接中的文档和其他资源"""
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue

            full_url = urljoin(base_url, href)
            extension = os.path.splitext(full_url)[1].lower()

            if extension in self.document_extensions:
                resources['file'].append({
                    'url': full_url,
                    'text': link.text.strip(),
                    'type': extension[1:] if extension else 'unknown'
                })
            elif extension and extension not in ['.html', '.htm', '.php', '.asp', '.aspx', '.jsp']:
                resources['other_resource'].append({
                    'url': full_url,
                    'text': link.text.strip(),
                    'type': extension[1:] if extension else 'unknown'
                })

        for link in soup.find_all('link'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                rel = link.get('rel', [])
                if isinstance(rel, list) and rel:
                    rel = rel[0]

                if rel == 'stylesheet' or full_url.endswith('.css'):
                    resources['other_resource'].append({
                        'url': full_url,
                        'type': 'css',
                        'rel': rel
                    })
                elif full_url.endswith(tuple(self.document_extensions)):
                    resources['documents'].append({
                        'url': full_url,
                        'type': os.path.splitext(full_url)[1][1:],
                        'rel': rel
                    })


def main():
    # 示例用法
    html_content = """
    <figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/1*JIY-WkvHT-xR_I1R0nryMw.png" /></figure><p>A defining feature of the 21st century, social platforms have shaped the reality we live in today. In their currently dominantly centralized format, social media platforms have brought out the best and worst human beings.</p><p>They also are the building blocks of megacorporations that use their power to lobby the democratically elected bodies to concentrate ever more power in their hands.</p><p>On the positive side, social platforms have enabled humans across the globe to communicate, exchange ideas, build collaboration, raise funds for any type of project, create local, national, or global community building, benefit social-minded projects, and many, many more highly positive outcomes. This was all a result of centralized social sharing, that is a social sharing system relying on a centralized social media platform.</p><p>Those are a hymn to the fundamental goodness of humanity.</p><p>Yet the global spread of social platforms also led to showing the ugly side of humans, from online bullying, contribution to the efficiency of terrorists and criminal organizations, created echo chambers where people became radicalized, boosted the spread of conspiracy theories of all kinds and many, many more highly harmful outcomes.</p><p>Those are a testimony to the power of the evil residing in each human.</p><p>So, in short, one could say that social platforms have only acted as an amplifier of human nature. However, this is discounting the ways social media platforms have denatured the natural flow of human exchanges for material gain. They tweaked social media sharing and artificially bloated engagement by prioritizing what is shown to viewers.</p><p>Maybe decentralized social platforms could indeed uncover the real balance between good and evil in the human psyche and decentralized social sharing could better reflect nature if it is not optimized for revenue..</p><p>With 82% of human beings connected to social platforms and spending an <a href="https://2key.me/Average-Time-Spent-On-Social-Media-In-2021By-Platform/z19yD">average of 36 min daily</a> on them, it has never been more critical to understand how those platforms affect our humanity.</p><p>So, let’s see what the difference between current social platforms and decentralized ones are, and maybe attempt to understand how those differences might shape the future if we shift to decentralized social media platforms.</p><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/0*ES04-DeU0EnttTzB" /></figure><h3>Breaking down the differences between centralized and decentralized platforms</h3><h4>1. Power concentration</h4><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/0*xz_chY97IZjsyThQ" /></figure><p>The primary success tool of today’s social media platform is that the power is concentrated in the hands of a small number of stakeholders enjoying near-absolute power on how to interact with their use.</p><p>In practice, this unabated power concentration has confirmed the adage “Power corrupts; absolute power corrupts absolutely.” From <a href="https://2key.me/Companies-Are-Making-Money-From-Our-Personal-Data-%E2%80%93-But-Cost/s2BYt">data appropriation</a> and <a href="https://2key.me/Facebook-Agrees-To-Pay-Record-5Billion-In-Privacy-Settlement-With-Ftc/x35RV">user productization</a> to <a href="https://2key.me/Facebook-Reveals-News-Feed-Experiment-To-Control-Emotions/RM1cC">running crowd mood control experiments</a> on unsuspecting users, mega social platforms used a variety of unsavory tactics to enrich their shareholders and heavily lobbied regulators to limit the reforms demanded by the public once their abuse came to light.</p><p>In stark contrast with these mega entities, decentralized social media platforms are applying some degree of governance by the users, and the most dedicated ones intend to switch to full user governance as soon as viably feasible.</p><h4>2. Users’ Privacy</h4><p>As collecting users’ data is an integral part of a centralized social media platforms revenue model, their default position is to <a href="https://2key.me/Privacy-Violations-%E2%80%93-Dark-Side-Social-Media/WkYAK">collect as much data as possible</a> within the legally admissible boundaries. This is what their shareholders demand, and this is what they do.</p><p>Decentralized social media platforms typically have no shareholders to pander to, as the revenue model is based on tokenomics where users are de facto owners through the platform tokens.</p><h4>3. Data Ownership</h4><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/0*k3hSnIXyT8VNyhg-" /></figure><p>Centralized social media platforms are keen to <a href="https://2key.me/Ownership-Content-In-Your-Digital-Life-%E2%80%93-Social-Media/wyWPq">ensure as much data ownership as possible</a> on as much data as possible, be it user-generated data or user-generated content. They can then repurpose all collected data to generate revenue without any care for the user’s consent, informed or not, and, more importantly, without compensation.</p><p>As decentralized social media platforms can leverage blockchain technology to perform multitudes of micropayment, it enables their user to <a href="https://2key.me/Future-Social-Media-Decentralized/T4At7">claim ownership of all their data</a> and grant detailed right of use for these data with the possibility to receive payment for that use.</p><h4>4. Revenue generation and distribution</h4><p>Centralized social media platforms shareholders are typically focused on maximizing revenue, even at the <a href="https://2key.me/Social-Media-Addiction-Addiction-Center/jc3R5">cost of their users’ well-being</a>. This is a direct result of the total separation between users and shareholders. Yes, shareholders might also be users, but they represent a microscopic fraction of the platform’s user base. Generated revenues are distributed exclusively to the shareholders, without a penny reaching the users.</p><p>On decentralized social media platforms, the entire logic is turned on its head. The users are generating the value, and whatever revenue this v<a href="https://hackernoon.com/why-a-decentralized-social-network-with-passive-income-potential-will-emerge-eventually-vg473e47">alue generated is shared with the users</a> in direct proportion to their input.</p><h4>5. Users vs. products</h4><figure><img alt="" src="https://cdn-images-1.medium.com/max/1013/1*SpSqFBr6h-S3q_D74LvyLQ.jpeg" /></figure><p>On a centralized social media platform, the main product is the users’ eyeballs that can be sold to advertisers. As such, the user is the product, and the product needs to be as productive as possible, which implies <a href="https://2key.me/Social-Media-Addiction-Its-Impact-Mediation-Intervention/waiAP">creating systems that hook the users</a> and keep them returning over and over again. The toxicity of this “gamification” process is obviously well known by their creators since they <a href="https://2key.me/Tech-Moguls-Invented-Social-Media-Have-Banned-Their-Children-From-It/YGrvV">do their utmost to shield their children</a> from it.</p><p>On decentralized social media platforms, the users have a say in the platform governance, and, as their own well-being is at stake, the likelihood of them being abused daily by the system is far less.</p><h4>6. Transparency</h4><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/0*1P868_-TGMu8xXGf" /></figure><p>Algorithms and other data pertaining to their efficiency and effect and their end goal are centralized social media platforms’ jealously guarded secrets. Not even legislators have the right to peek beyond the veil and check what they are actually up to. Shrouded in their secrecy, they are unilaterally manipulating public opinion, leading to <a href="https://2key.me/Socialmedia-Algorithms-Rule-How-We-See-World-Good-Luck-Trying-To-Stop-Them/Nva2D">ineffective pleas from public figures</a> to act responsibly.</p><p>In stark contrast, decentralized social media platforms are <a href="https://2key.me/Decentralized-Social-Media-Improving-User-Experience-Dzone-Security/nDDlb">ruled by smart contracts</a>, the aim of which is clearly stated, and these smart contracts are typically audited by third parties.</p><h4>7. Legal Rights</h4><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/1*j2ym9JMQiwXlWGdPle0lsg.jpeg" /></figure><p>Centralized social media platforms have a hefty budget to finance the highest-paid lawyers and lobbyists’ services so that they can ensure both the best legal representation and close access to regulators’ ears. In short, they can, and do, use their power to obtain advantages such as, for example,<a href="https://2key.me/Opinion-Heres-Why-Facebooks-Tax-Breaks-Are-Thoroughly-Undeserved/tS49m"> tax exemptions</a> or evading fines.</p><p>The tide, however, seems to be turning, as <a href="https://2key.me/Ftc-Slaps-Facebook-With-5Billion-Fine-Forces-New-Privacy-Controls/lfrLN">fines for abuse of privacy rights are reaching painful amounts</a> and <a href="https://2key.me/Inclusive-Framework-Statement-Agrees-Taxation-Digital-Economy-Global-Minimum/wifVt">tax exemptions are coming to an end.</a></p><p>In stark contrast, decentralized social media platforms are startups with little funding, affordable legal representation, and needing to keep their legal expenses to a strict minimum. Lobbying is not even on the horizon. To make matters worse, decentralized social media platforms typically rely on their own issued tokens as a source of financing, and the legal status of cryptocurrencies is in flux, subject to change that might sink the project.</p><h3>The Future of Decentralized Social Media Sharing</h3><p>Despite all these obstacles, <a href="https://2key.me/Best-Blockchainbased-Decentralized-Social-Media-Networks/gyW0T">they keep growing</a>, both in the number of platforms and in the number of users.</p><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/0*4CL4Mln-xn32cpUU" /></figure><p>As the decentralized movement grows, social media platforms will integrate other DApps such as <a href="https://2key.io/">2key.io</a> that enables users to monetize their sharing activity by turning any link they want to share into a <a href="https://www.2key.network/">SmartLink</a>, enabling users to earn to share.</p><p>Currently, SmartLinks are already being integrated into publishing platforms through the <a href="https://www.2key.network/embed-button">Refer &amp; Earn button</a>, adopted by publications such as <a href="https://coinchapter.com/">coinchapter</a>, <a href="https://cberry.net/post/lending-pro-change-log">cherry.net</a>, or <a href="https://www.cryptojobsdaily.com/">cryptojobsdaily</a>, to name a few.</p><figure><img alt="" src="https://cdn-images-1.medium.com/max/1024/0*rCndu4pw5FL2WD98" /></figure><p>In the near future, Share and Earn buttons will be made available to decentralized social media platforms that want to maximize their users’ passive income potential.</p><p>In today’s reality, megacorporations owning social platforms are waging a relentless battle against a myriad of budding decentralized social platforms. Yet, the strength of megacorporations resides in their high concentration of users, the very same users they feel free to use and abuse for profit.</p><img src="https://medium.com/_/stat?event=post.clientViewed&referrerSource=full_rss&postId=ab412c5fc792" width="1" height="1" alt=""><hr><p><a href="https://medium.com/2key/how-shifting-from-centralized-to-decentralized-social-sharing-changes-reality-ab412c5fc792">How Shifting from Centralized to Decentralized Social Sharing Changes Reality</a> was originally published in <a href="https://medium.com/2key">2key</a> on Medium, where people are continuing the conversation by highlighting and responding to this story.</p>
    """

    extractor = HTMLResourceExtractor()
    resources = extractor.extract_resources(html_content)

    for resources_type, v in resources.items():
        if v:
            for item in v:
                print(f"{resources_type}: {item.get("url")}")


if __name__ == "__main__":
    main()

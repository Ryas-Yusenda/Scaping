import * as cheerio from "cheerio";
import puppeteerExtra from "puppeteer-extra";
import stealthPlugin from "puppeteer-extra-plugin-stealth";
import fs from "fs/promises";

async function getGoogleMapsData() {
    puppeteerExtra.use(stealthPlugin());

    // Set user agent
    const userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36";

    // Launch browser
    const browser = await puppeteerExtra.launch({
        headless: false, // Set to true for headless mode
        args: [
            `--user-agent=${userAgent}`,
            // "--window-size=1920,1080",
            "--ignore-certificate-errors",
            "--allow-running-insecure-content",
            "--disable-extensions",
            "--proxy-server='direct://'",
            "--proxy-bypass-list=*",
            // "--start-maximized",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ],
    });

    const page = await browser.newPage();
    const query = "coffee shop di yogyakarta";

    try {
        // Go to the Google Maps page
        await page.goto(`https://www.google.com/maps/search/${query.split(" ").join("+")}`);

        // Scroll to the end of the page
        await autoScroll(page);

        // Get HTML content
        const html = await page.content();

        // Then close the browser
        await browser.close();

        // Extract relevant information using Cheerio
        const businesses = extractBusinessInfo(html);

        // save to json
        await saveToJson(businesses);

        console.log("Done!");

        return businesses;
    } catch (error) {
        console.error("Something went wrong!", error);
        return [];
    } finally {
        // Close the browser
        await browser.close();
    }
}

async function autoScroll(page) {
    await page.evaluate(async () => {
        // Element Scrollable Area (List of Location)
        const wrapper = document.querySelector('div[role="feed"]');
        const distance = 1000;
        const scrollDelay = 4000;

        await new Promise((resolve, reject) => {
            let totalHeight = 0;

            let timer = setInterval(async () => {
                let scrollHeightBefore = wrapper.scrollHeight;
                wrapper.scrollBy(0, distance);
                totalHeight += distance;

                if (totalHeight >= scrollHeightBefore) {
                    // Wait for content to load
                    await new Promise((resolve) => setTimeout(resolve, scrollDelay));

                    // jika div terakhir di wrapper tidak terdapat element <a>, tetapi ada element <span>, maka berhenti scroll
                    const lastChild = wrapper.lastChild;
                    const lastChildAnchor = lastChild.querySelector('a');
                    const lastChildSpan = lastChild.querySelector('span');
                    if (!lastChildAnchor && lastChildSpan && (wrapper.scrollHeight <= scrollHeightBefore)) {
                        resolve();
                        clearInterval(timer);
                    }
                }
            }, 1000);
        });
    });
};

function extractBusinessInfo(html) {
    const $ = cheerio.load(html);
    const businesses = [];

    $("a[href*='/maps/place/']").each((i, el) => {
        const parent = $(el).parent();

        const name = parent.find("div.fontHeadlineSmall").text();

        const bodyDiv = parent.find("div.fontBodyMedium").first();

        const lastChild = bodyDiv.children().last();
        const [hours, address] = lastChild.text().split(" ⋅ ").map(item => item.trim());

        const ratingText = parent.find("span.fontBodyMedium > span").attr("aria-label");
        const imgUrl = parent.find("img").attr("src");
        const googleUrl = $(el).attr("href");

        businesses.push({
            name,
            address,
            hours,
            ratingText,
            imgUrl,
            googleUrl,
        });
    });

    return businesses;
}

async function saveToJson(data) {
    try {
        await fs.writeFile("data.json", JSON.stringify({ businesses: data }, null, 2));
        // await fs.writeFile("data.json", JSON.stringify(data));
        console.log("File has been created");
    } catch (err) {
        console.error(err);
    }
}

// Call the main function
getGoogleMapsData();

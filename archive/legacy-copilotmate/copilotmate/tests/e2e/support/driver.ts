import { Builder, WebDriver } from "selenium-webdriver";
import chrome from "selenium-webdriver/chrome";

const isBrowserStack = process.env.SELENIUM_REMOTE === "browserstack";

function requiredEnvironmentVariable(name: string): string {
  const value = process.env[name];

  if (!value) {
    throw new Error(`${name} is required for BrowserStack test runs.`);
  }

  return value;
}

export async function createDriver(): Promise<WebDriver> {
  if (!isBrowserStack) {
    const options = new chrome.Options();

    if (process.env.HEADLESS !== "false") {
      options.addArguments("--headless=new");
    }

    options.addArguments(
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--window-size=1440,1000",
    );

    return new Builder()
      .forBrowser("chrome")
      .setChromeOptions(options)
      .build();
  }

  const username = requiredEnvironmentVariable("BROWSERSTACK_USERNAME");
  const accessKey = requiredEnvironmentVariable("BROWSERSTACK_ACCESS_KEY");
  const browserName = process.env.BROWSERSTACK_BROWSER ?? "Chrome";
  const browserVersion = process.env.BROWSERSTACK_BROWSER_VERSION ?? "latest";
  const os = process.env.BROWSERSTACK_OS ?? "Windows";
  const osVersion = process.env.BROWSERSTACK_OS_VERSION ?? "11";

  return new Builder()
    .usingServer("https://hub.browserstack.com/wd/hub")
    .withCapabilities({
      browserName,
      browserVersion,
      "bstack:options": {
        os,
        osVersion,
        userName: username,
        accessKey,
        projectName: process.env.BROWSERSTACK_PROJECT_NAME ?? "CopilotMate",
        buildName:
          process.env.BROWSERSTACK_BUILD_NAME ??
          `CopilotMate local ${new Date().toISOString()}`,
        sessionName: `Todo workflows - ${browserName} ${browserVersion}`,
        local: true,
        localIdentifier: process.env.BROWSERSTACK_LOCAL_IDENTIFIER,
        debug: true,
        networkLogs: true,
        video: true,
        consoleLogs: "errors",
      },
    })
    .build();
}

export async function setBrowserStackSessionStatus(
  driver: WebDriver,
  status: "passed" | "failed",
  reason: string,
): Promise<void> {
  if (!isBrowserStack) {
    return;
  }

  const payload = JSON.stringify({
    action: "setSessionStatus",
    arguments: { status, reason },
  });

  await driver.executeScript(`browserstack_executor: ${payload}`);
}

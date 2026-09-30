import { expect } from "chai";
import { By, until, WebDriver, WebElement } from "selenium-webdriver";
import {
  createDriver,
  setBrowserStackSessionStatus,
} from "./support/driver";

const baseUrl = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const waitTimeout = 15_000;

async function findTaskByTitle(
  driver: WebDriver,
  title: string,
): Promise<WebElement> {
  const task = await driver.wait(async () => {
    const titleElements = await driver.findElements(
      By.css('[data-testid="todo-task-title"]'),
    );

    for (const titleElement of titleElements) {
      if ((await titleElement.getText()) === title) {
        return titleElement.findElement(
          By.xpath('./ancestor::*[@data-testid="todo-task"][1]'),
        );
      }
    }

    return false;
  }, waitTimeout, `Could not find task titled "${title}".`);

  return task as WebElement;
}

async function addTask(driver: WebDriver, title: string): Promise<WebElement> {
  const titleInput = await driver.findElement(
    By.css('[data-testid="todo-title-input"]'),
  );

  await titleInput.sendKeys(title);
  await driver
    .findElement(By.css('[data-testid="todo-add-button"]'))
    .click();

  return findTaskByTitle(driver, title);
}

async function taskIsAbsent(driver: WebDriver, title: string): Promise<boolean> {
  const titleElements = await driver.findElements(
    By.css('[data-testid="todo-task-title"]'),
  );

  for (const titleElement of titleElements) {
    if ((await titleElement.getText()) === title) {
      return false;
    }
  }

  return true;
}

describe("CopilotMate Todo workflows", function () {
  let driver: WebDriver;

  beforeEach(async function () {
    driver = await createDriver();
    await driver.get(`${baseUrl}/todo`);
    await driver.wait(
      until.elementLocated(By.css('[data-testid="todo-title-input"]')),
      waitTimeout,
    );
  });

  afterEach(async function () {
    if (!driver) {
      return;
    }

    const passed = this.currentTest?.state === "passed";
    const reason = passed
      ? `${this.currentTest?.title ?? "Todo workflow"} passed.`
      : this.currentTest?.err?.message ?? "Todo workflow failed.";

    try {
      await setBrowserStackSessionStatus(
        driver,
        passed ? "passed" : "failed",
        reason.slice(0, 255),
      );
    } finally {
      await driver.quit();
    }
  });

  it("adds a new task", async function () {
    const title = `Selenium add ${Date.now()}`;
    const task = await addTask(driver, title);

    expect(await task.isDisplayed()).to.equal(true);
  });

  it("marks a task as complete", async function () {
    const title = `Selenium complete ${Date.now()}`;
    const task = await addTask(driver, title);
    const checkbox = await task.findElement(By.css('[role="checkbox"]'));

    await checkbox.click();
    await driver.wait(
      async () => {
        const updatedTask = await findTaskByTitle(driver, title);
        const updatedCheckbox = await updatedTask.findElement(
          By.css('[role="checkbox"]'),
        );

        return (await updatedCheckbox.getAttribute("aria-checked")) === "true";
      },
      waitTimeout,
      "The task did not enter the completed state.",
    );

    const updatedTask = await findTaskByTitle(driver, title);
    const titleElement = await updatedTask.findElement(
      By.css('[data-testid="todo-task-title"]'),
    );
    expect(await titleElement.getAttribute("class")).to.include("line-through");
  });

  it("changes a task priority", async function () {
    const title = `Selenium priority ${Date.now()}`;
    const task = await addTask(driver, title);
    const priority = await task.findElement(
      By.css('[data-testid="todo-task-priority"]'),
    );

    await priority.findElement(By.css('option[value="high"]')).click();
    await driver.wait(
      async () => (await priority.getAttribute("value")) === "high",
      waitTimeout,
      "The task priority did not change to high.",
    );

    expect(await priority.getAttribute("value")).to.equal("high");
  });

  it("deletes a task", async function () {
    const title = `Selenium delete ${Date.now()}`;
    const task = await addTask(driver, title);

    await task
      .findElement(By.css('[data-testid="todo-task-delete"]'))
      .click();
    await driver.wait(
      () => taskIsAbsent(driver, title),
      waitTimeout,
      "The task was not removed.",
    );

    expect(await taskIsAbsent(driver, title)).to.equal(true);
  });
});

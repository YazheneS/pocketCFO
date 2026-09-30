import {
  CopilotRuntime,
  GroqAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { Groq } from "groq-sdk";

const remoteActionUrl =
  process.env.COPILOTKIT_REMOTE_ACTION_URL ?? "http://127.0.0.1:8000/copilotkit";
const groqModel = process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile";

const runtime = new CopilotRuntime({
  remoteActions: [
    {
      url: remoteActionUrl,
    },
  ],
});

export const dynamic = "force-dynamic";

export const POST = async (req: NextRequest) => {
  const apiKey = process.env.GROQ_API_KEY;

  if (!apiKey) {
    return Response.json(
      {
        error:
          "GROQ_API_KEY is required to use the CopilotKit runtime endpoint.",
      },
      { status: 500 }
    );
  }

  const serviceAdapter = new GroqAdapter({
    groq: new Groq({ apiKey }),
    model: groqModel,
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};

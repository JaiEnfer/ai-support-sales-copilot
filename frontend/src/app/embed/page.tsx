import { EmbeddedChat } from "@/components/embedded-chat";
import { DEFAULT_COMPANY_ID } from "@/lib/copilot";

type EmbedPageProps = {
  searchParams: Promise<{
    company?: string;
    title?: string;
    subtitle?: string;
    apiKey?: string;
  }>;
};

export default async function EmbedPage({ searchParams }: EmbedPageProps) {
  const params = await searchParams;

  return (
    <EmbeddedChat
      companyId={params.company || DEFAULT_COMPANY_ID}
      title={params.title || "AI Website Assistant"}
      subtitle={
        params.subtitle ||
        "Hi! I can answer questions using this company's uploaded knowledge base."
      }
      apiKey={params.apiKey}
    />
  );
}

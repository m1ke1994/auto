import { getSectionContent, parseJsonContent } from "./publicSite"

export async function getFooterSettings() {
  const content = await getSectionContent("footer")
  return {
    ...content,
    links: parseJsonContent(content, "links_json", []),
  }
}

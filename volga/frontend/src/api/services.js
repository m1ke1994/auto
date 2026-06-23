import { getJsonSectionItems } from "./publicSite"

export async function getServices() {
  return await getJsonSectionItems("services")
}

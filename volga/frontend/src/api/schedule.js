import { getJsonSectionItems } from "./publicSite"

export async function getSchedule() {
  return await getJsonSectionItems("schedule")
}

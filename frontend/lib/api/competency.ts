import { CompetencyState } from "./types";
import { client } from "./client";
import jsoMockData from "@/lib/mock/officer-jso.json";
import newOfficerMockData from "@/lib/mock/officer-new.json";

export function getCompetencyStateSync(
  persona: "jso" | "new" = "jso"
): CompetencyState {
  if (persona === "new") {
    return newOfficerMockData as unknown as CompetencyState;
  }
  return jsoMockData as unknown as CompetencyState;
}

export async function getCompetencyState(
  persona: "jso" | "new" = "jso"
): Promise<CompetencyState> {
  const useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

  if (useMock) {
    // Return structured sandbox data synchronously wrapped in promise
    return getCompetencyStateSync(persona);
  }

  // Live API call when NEXT_PUBLIC_USE_MOCK is set to "false"
  return client.get<CompetencyState>("/api/competency/state");
}

import { CompetencyState } from "./types";
import { client } from "./client";
import jsoMockData from "@/lib/mock/officer-jso.json";
import newOfficerMockData from "@/lib/mock/officer-new.json";

export async function getCompetencyState(
  persona: "jso" | "new" = "jso"
): Promise<CompetencyState> {
  const useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

  if (useMock) {
    // Return structured sandbox data
    if (persona === "new") {
      return newOfficerMockData as unknown as CompetencyState;
    }
    return jsoMockData as unknown as CompetencyState;
  }

  // Live API call when NEXT_PUBLIC_USE_MOCK is set to "false"
  return client.get<CompetencyState>("/api/competency/state");
}

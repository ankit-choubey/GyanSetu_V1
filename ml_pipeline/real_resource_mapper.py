import json
import os
import time

from ml_pipeline.concept_extractor import extract_concepts
from ml_pipeline.competency_mapper import map_competencies


# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Real/public data paths
IGOT_PATH = os.path.join(
    BASE_DIR,
    "real_data",
    "data",
    "igot_course_catalog.json"
)

NSSTA_PATH = os.path.join(
    BASE_DIR,
    "real_data",
    "data",
    "nssta_tpac_programmes.json"
)


# Output path
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "real_data",
    "data",
    "real_resource_competency_mappings.json"
)


# Rate-limit configuration
RETRY_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 5
BETWEEN_RESOURCES_SECONDS = 2


def load_json(path):
    """Load a JSON file."""

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"JSON file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_resource_text(resource):
    """
    Build the text that will be sent to the concept extractor.

    Different resource types use different fields, so collect
    all relevant learning-related fields.
    """

    fields = [
        resource.get("course_title"),
        resource.get("programme_title"),
        resource.get("description"),
        resource.get("topic"),
        resource.get("content"),
        resource.get("competencies"),
        resource.get("tags"),
        resource.get("target_audience"),
    ]

    text_parts = []

    for field in fields:

        if field is None:
            continue

        if isinstance(field, list):
            field = ", ".join(str(item) for item in field)

        field = str(field).strip()

        if field:
            text_parts.append(field)

    return "\n".join(text_parts)


def load_real_resources():
    """
    Load all real/public learning resources from iGOT and NSSTA.
    """

    # iGOT
    igot_data = load_json(IGOT_PATH)

    if not isinstance(igot_data, dict):
        raise ValueError(
            "Invalid iGOT JSON structure: expected a dictionary."
        )

    igot_resources = igot_data.get("courses", [])

    if not isinstance(igot_resources, list):
        raise ValueError(
            "Invalid iGOT JSON structure: 'courses' must be a list."
        )


    # NSSTA
    nssta_resources = load_json(NSSTA_PATH)

    if not isinstance(nssta_resources, list):
        raise ValueError(
            "Invalid NSSTA JSON structure: expected a list."
        )


    resources = []


    # Add iGOT resources
    for resource in igot_resources:

        if not isinstance(resource, dict):
            print("Warning: skipping invalid iGOT resource.")
            continue

        resource_copy = dict(resource)

        resource_copy["resource_type"] = "iGOT course"

        resource_copy.setdefault(
            "data_source",
            "[REAL/PUBLIC DATA]"
        )

        resources.append(resource_copy)


    # Add NSSTA resources
    for resource in nssta_resources:

        if not isinstance(resource, dict):
            print("Warning: skipping invalid NSSTA resource.")
            continue

        resource_copy = dict(resource)

        resource_copy["resource_type"] = "NSSTA TPAC programme"

        resource_copy.setdefault(
            "data_source",
            "[REAL/PUBLIC DATA]"
        )

        resources.append(resource_copy)


    return resources


def resource_key(resource):
    """
    Create a stable key for identifying a resource.

    This allows the pipeline to resume without processing
    already successful resources again.
    """

    resource_type = resource.get(
        "resource_type",
        ""
    )

    title = (
        resource.get("course_title")
        or resource.get("programme_title")
        or ""
    )

    target_audience = resource.get(
        "target_audience",
        ""
    )

    return (
        f"{resource_type}|"
        f"{title}|"
        f"{target_audience}"
    )


def load_existing_results():
    """
    Load previously generated results if they exist.
    """

    if not os.path.exists(OUTPUT_PATH):
        return []

    try:

        data = load_json(OUTPUT_PATH)

        if isinstance(data, list):
            return data

        print(
            "Warning: existing output is not a list. "
            "Starting fresh."
        )

        return []

    except Exception as error:

        print(
            f"Warning: could not load existing output: {error}"
        )

        return []


def save_results(results):
    """Save mapping results safely."""

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2
        )


def call_with_retry(function, description):
    """
    Call an LLM function with retry handling.

    Rate-limit errors are retried after a short delay.
    Other errors are also retried, but the error is reported.
    """

    for attempt in range(1, RETRY_ATTEMPTS + 1):

        try:

            return function()

        except Exception as error:

            error_text = str(error)

            print(
                f"  {description} failed "
                f"(attempt {attempt}/{RETRY_ATTEMPTS})"
            )

            print(
                f"  Error: {error_text}"
            )

            if attempt < RETRY_ATTEMPTS:

                print(
                    f"  Waiting {RETRY_WAIT_SECONDS} seconds "
                    f"before retry..."
                )

                time.sleep(RETRY_WAIT_SECONDS)

            else:

                print(
                    f"  {description} failed after "
                    f"{RETRY_ATTEMPTS} attempts."
                )

                return None


def create_result_record(
    resource,
    title,
    status,
    concepts=None,
    competency_mappings=None,
    error=None
):
    """Create a consistent output record."""

    result = {
        "resource_type": resource.get(
            "resource_type"
        ),

        "title": title,

        "source_url": resource.get(
            "source_url"
        ),

        "course_url": resource.get(
            "course_url"
        ),

        "year": resource.get(
            "year"
        ),

        "target_audience": resource.get(
            "target_audience"
        ),

        "data_source": resource.get(
            "data_source",
            "[REAL/PUBLIC DATA]"
        ),

        "status": status,

        "concepts": concepts or [],

        "competency_mappings": competency_mappings or [],
    }

    if error:
        result["error"] = error

    return result


def map_real_resources():
    """
    Extract concepts and map competencies for real/public resources.

    The pipeline is resumable:
    successful resources from an existing output file are reused.
    """

    resources = load_real_resources()

    existing_results = load_existing_results()


    # Build lookup of successful previous results
    successful_results = {}

    for result in existing_results:

        if result.get("status", "success") == "success":

            key = (
                f"{result.get('resource_type', '')}|"
                f"{result.get('title', '')}|"
                f"{result.get('target_audience', '')}"
            )

            successful_results[key] = result


    # Start with existing results so successful records are preserved
    results = list(successful_results.values())


    print("=" * 70)
    print("REAL/PUBLIC RESOURCE COMPETENCY MAPPING")
    print("=" * 70)

    print(
        f"Total resources: {len(resources)}"
    )

    print(
        f"Existing successful results: "
        f"{len(successful_results)}"
    )

    print("=" * 70)


    for index, resource in enumerate(
        resources,
        start=1
    ):

        title = (
            resource.get("course_title")
            or resource.get("programme_title")
            or f"Resource {index}"
        )

        resource_type = resource.get(
            "resource_type",
            "Unknown"
        )

        key = resource_key(resource)


        # Skip already-successful resources
        if key in successful_results:

            print()
            print(
                f"[{index}/{len(resources)}] "
                f"{resource_type}: {title}"
            )

            print(
                "  Already processed successfully. Skipping."
            )

            continue


        print()
        print(
            f"[{index}/{len(resources)}] "
            f"{resource_type}: {title}"
        )


        resource_text = build_resource_text(
            resource
        )


        if not resource_text:

            print(
                "  Skipped: no usable text."
            )

            result = create_result_record(
                resource=resource,
                title=title,
                status="skipped",
                error="No usable text."
            )

            results.append(result)

            save_results(results)

            continue


        print(
            f"  Text length: "
            f"{len(resource_text)} characters"
        )


        # ---------------------------------------------------------
        # Concept extraction
        # ---------------------------------------------------------

        print(
            "  Extracting concepts..."
        )

        concepts = call_with_retry(
            lambda: extract_concepts(
                resource_text
            ),
            "Concept extraction"
        )


        if concepts is None:

            result = create_result_record(
                resource=resource,
                title=title,
                status="failed_concept_extraction",
                error="Concept extraction failed after retries."
            )

            results.append(result)

            save_results(results)

            continue


        print(
            f"  Concepts found: "
            f"{len(concepts)}"
        )


        # ---------------------------------------------------------
        # Competency mapping
        # ---------------------------------------------------------

        print(
            "  Mapping competencies..."
        )

        competency_mappings = call_with_retry(
            lambda: map_competencies(
                concepts
            ),
            "Competency mapping"
        )


        if competency_mappings is None:

            result = create_result_record(
                resource=resource,
                title=title,
                status="failed_competency_mapping",
                concepts=concepts,
                error="Competency mapping failed after retries."
            )

            results.append(result)

            save_results(results)

            continue


        print(
            f"  Competencies mapped: "
            f"{len(competency_mappings)}"
        )


        # ---------------------------------------------------------
        # Successful result
        # ---------------------------------------------------------

        result = create_result_record(
            resource=resource,
            title=title,
            status="success",
            concepts=concepts,
            competency_mappings=competency_mappings
        )


        results.append(result)

        successful_results[key] = result

        save_results(results)


        # Give the rate limit some breathing room
        if index < len(resources):

            print(
                f"  Waiting "
                f"{BETWEEN_RESOURCES_SECONDS} seconds..."
            )

            time.sleep(
                BETWEEN_RESOURCES_SECONDS
            )


    # -------------------------------------------------------------
    # Final summary
    # -------------------------------------------------------------

    success_count = sum(
        1
        for result in results
        if result.get("status") == "success"
    )

    failed_count = sum(
        1
        for result in results
        if result.get("status", "").startswith("failed")
    )

    skipped_count = sum(
        1
        for result in results
        if result.get("status") == "skipped"
    )


    print()
    print("=" * 70)
    print("MAPPING COMPLETE")
    print("=" * 70)

    print(
        f"Total source resources: {len(resources)}"
    )

    print(
        f"Successful: {success_count}"
    )

    print(
        f"Failed: {failed_count}"
    )

    print(
        f"Skipped: {skipped_count}"
    )

    print(
        f"Output records: {len(results)}"
    )

    print()
    print(
        f"Output saved to:\n{OUTPUT_PATH}"
    )

    print("=" * 70)


    return results


if __name__ == "__main__":
    map_real_resources()
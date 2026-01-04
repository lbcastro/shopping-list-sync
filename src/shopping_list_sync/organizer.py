"""Shopping list organization using OpenAI categorization."""

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from openai import OpenAI
from todoist_api_python.api import TodoistAPI, Task

from shopping_list_sync.config import settings, load_categories


def create_error_task(todoist_client: TodoistAPI, error_message: str) -> None:
    """Create a task in Todoist for an error that needs attention.

    Only creates task if ERROR_HANDLING_MODE includes 'task' and TODOIST_SYSTEM_PROJECT_ID is configured.
    """
    if settings.ERROR_HANDLING_MODE not in ('task', 'both'):
        return

    if not settings.TODOIST_SYSTEM_PROJECT_ID:
        logger.warning(
            "ERROR_HANDLING_MODE is set to create tasks, but TODOIST_SYSTEM_PROJECT_ID is not configured"
        )
        return

    try:
        # Check for existing error task
        tasks = todoist_client.get_tasks(project_id=settings.TODOIST_SYSTEM_PROJECT_ID)
        existing_task = next(
            (t for t in tasks if "Shopping List Sync Error" in t.content and not t.is_completed),
            None
        )

        if existing_task:
            logger.info("Error task already exists in Todoist")
            return

        # Create new error task
        task_content = f"🔧 Shopping List Sync Error\n\nError occurred at {datetime.now().isoformat()}\n\n{error_message}"
        todoist_client.add_task(
            content=task_content,
            project_id=settings.TODOIST_SYSTEM_PROJECT_ID,
            priority=4,  # Highest priority
            due_string="today"
        )
        logger.info("Created error task in Todoist")

    except Exception as e:
        logger.error(f"Failed to create error task in Todoist: {e}")


def setup_todoist_resources(
    todoist_client: TodoistAPI,
    categories_config: Dict
) -> tuple[str, Dict[str, str]]:
    """Set up required Todoist projects and sections based on configuration.

    Args:
        todoist_client: Initialized Todoist API client
        categories_config: Category configuration from YAML

    Returns:
        Tuple of (project_id, section_dict) where section_dict maps category names to section IDs
    """
    # Get or create shopping list project
    if settings.TODOIST_SHOPPING_PROJECT_ID:
        try:
            shopping_project = todoist_client.get_project(
                project_id=settings.TODOIST_SHOPPING_PROJECT_ID
            )
        except Exception:
            logger.warning(
                f"Shopping list project with ID {settings.TODOIST_SHOPPING_PROJECT_ID} not found, "
                f"falling back to name search..."
            )
            shopping_project = None
    else:
        shopping_project = None

    if not shopping_project:
        projects = todoist_client.get_projects()
        shopping_project = next(
            (p for p in projects if p.name == settings.TODOIST_SHOPPING_PROJECT_NAME),
            None
        )

    if not shopping_project:
        logger.warning(
            f"Shopping list project '{settings.TODOIST_SHOPPING_PROJECT_NAME}' not found, creating it..."
        )
        shopping_project = todoist_client.add_project(name=settings.TODOIST_SHOPPING_PROJECT_NAME)

    # Get existing sections
    sections = todoist_client.get_sections(project_id=shopping_project.id)
    section_dict = {}

    # Create or get sections based on YAML config
    for category_key, category_config in categories_config.items():
        emoji = category_config['emoji']
        # Convert category key to title case (e.g., "meat_seafood" -> "Meat Seafood")
        category_name = category_key.replace('_', ' ').title()
        section_name = f"{emoji} {category_name}"

        section = next((s for s in sections if s.name == section_name), None)

        if not section:
            logger.info(f"Section '{section_name}' not found, creating it...")
            section = todoist_client.add_section(
                project_id=shopping_project.id,
                name=section_name
            )

        section_dict[category_key] = section.id

    return shopping_project.id, section_dict


def get_unlabeled_items(todoist_client: TodoistAPI, project_id: str) -> List[Task]:
    """Get all tasks without section assignments from the shopping list."""
    tasks = todoist_client.get_tasks(project_id=project_id)
    return [task for task in tasks if not task.section_id and not task.parent_id]


def categorize_items(
    openai_client: OpenAI,
    items: List[Task],
    categories_config: Dict
) -> Dict[str, List[Task]]:
    """Categorize shopping items using OpenAI.

    Args:
        openai_client: Initialized OpenAI client
        items: List of uncategorized tasks
        categories_config: Category configuration from YAML

    Returns:
        Dictionary mapping category keys to lists of tasks
    """
    if not items:
        return {}

    # Build category descriptions from config
    categories_desc = []
    for category_key, category_config in categories_config.items():
        emoji = category_config['emoji']
        category_name = category_key.replace('_', ' ').title()
        keywords = category_config.get('keywords', [])
        keywords_str = ', '.join(keywords[:5]) if keywords else ''
        desc = f"- {category_name} ({emoji})"
        if keywords_str:
            desc += f": {keywords_str}"
        categories_desc.append(desc)

    categories_list = '\n'.join(categories_desc)

    # Prepare items for OpenAI
    items_text = "\n".join(f"- {task.content}" for task in items)

    system_prompt = f"""You are a helpful shopping list assistant. Your task is to categorize shopping items into supermarket sections.

Use these categories ONLY:
{categories_list}

For items that don't fit any category, use "Other"."""

    user_prompt = f"""Here are the shopping items:

{items_text}

Categorize each item into one of the specified sections. Format your response as JSON with this structure:
{{
    "Produce": ["item1", "item2"],
    "Other": ["item3"],
    ...
}}

Only include categories that have items. Match items EXACTLY as provided. Use category names without emojis in the JSON keys."""

    try:
        completion = openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=1,
        )

        response_data = completion.choices[0].message.content
        category_to_items = eval(response_data)  # Safe since we specified json_object format

        # Map items back to their Task objects
        # Need to match category names from JSON (Title Case) to config keys (snake_case)
        categorized_items = {}
        for category_name, item_names in category_to_items.items():
            # Convert category name back to snake_case key
            category_key = category_name.lower().replace(' ', '_')

            # Find matching tasks
            matching_tasks = [
                task for task in items
                if any(item.lower() in task.content.lower() for item in item_names)
            ]
            if matching_tasks:
                categorized_items[category_key] = matching_tasks

        return categorized_items

    except Exception as e:
        logger.error(f"Failed to categorize items using OpenAI: {e}")
        raise


def get_existing_items(todoist_client: TodoistAPI, project_id: str) -> List[str]:
    """Get a list of items already in the shopping list (normalized for comparison)."""
    tasks = todoist_client.get_tasks(project_id=project_id)
    # Normalize strings: lowercase and stripped
    return [
        task.content.lower().strip()
        for task in tasks
        if task.section_id or task.parent_id
    ]


def organize_shopping_list():
    """Main function to organize the shopping list."""
    try:
        logger.info("Starting shopping list organization...")

        # Initialize API clients
        todoist_client = TodoistAPI(settings.TODOIST_API_KEY)

        try:
            openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            if settings.ERROR_HANDLING_MODE in ('log', 'both'):
                logger.error(f"OpenAI initialization error: {str(e)}")
            if settings.ERROR_HANDLING_MODE in ('task', 'both'):
                create_error_task(todoist_client, f"Failed to initialize OpenAI client: {str(e)}")
            return

        # Load categories from YAML
        try:
            categories_config = load_categories()
        except Exception as e:
            logger.error(f"Failed to load categories configuration: {e}")
            return

        # Set up Todoist resources
        project_id, section_dict = setup_todoist_resources(todoist_client, categories_config)

        # Get unlabeled items
        unlabeled_items = get_unlabeled_items(todoist_client, project_id)
        if not unlabeled_items:
            logger.info("No unlabeled items found in shopping list.")
            return

        logger.info(f"Found {len(unlabeled_items)} unlabeled items")

        # Get existing categorized items for duplicate checking
        existing_items = get_existing_items(todoist_client, project_id)

        # Filter out duplicates
        unique_unlabeled_items = []
        for item in unlabeled_items:
            normalized_content = item.content.lower().strip()
            if normalized_content in existing_items:
                logger.info(f"Duplicate item found: '{item.content}'. Deleting...")
                try:
                    todoist_client.delete_task(task_id=item.id)
                    logger.info(f"Deleted duplicate item: {item.content}")
                except Exception as e:
                    logger.error(f"Failed to delete duplicate item {item.content}: {e}")
            else:
                unique_unlabeled_items.append(item)

        if not unique_unlabeled_items:
            logger.info("All new items were duplicates. Nothing to categorize.")
            return

        logger.info(f"Proceeding to categorize {len(unique_unlabeled_items)} unique items")

        try:
            # Categorize items
            categorized_items = categorize_items(
                openai_client,
                unique_unlabeled_items,
                categories_config
            )
        except Exception as e:
            logger.error(f"Failed to categorize items using OpenAI: {e}")
            if settings.ERROR_HANDLING_MODE in ('log', 'both'):
                logger.error(f"OpenAI categorization error: {str(e)}")
            if settings.ERROR_HANDLING_MODE in ('task', 'both'):
                create_error_task(todoist_client, f"Failed to categorize items using OpenAI: {str(e)}")
            return

        # Move items to their sections
        for category_key, items in categorized_items.items():
            if items and category_key in section_dict:
                section_id = section_dict[category_key]
                category_name = category_key.replace('_', ' ').title()

                for item in items:
                    try:
                        todoist_client.update_task(
                            task_id=item.id,
                            section_id=section_id
                        )
                        logger.info(f"Moved item to {category_name}: {item.content}")
                    except Exception as e:
                        logger.error(f"Failed to move item {item.content} to section {section_id}: {e}")
                        # Try recreation as fallback
                        try:
                            logger.info(f"Attempting to recreate task {item.content} in new section...")
                            new_task = todoist_client.add_task(
                                content=item.content,
                                project_id=project_id,
                                section_id=section_id
                            )
                            logger.info(f"Created new task in {category_name}: {new_task.content}")

                            try:
                                todoist_client.delete_task(task_id=item.id)
                                logger.info(f"Deleted original task: {item.content}")
                            except Exception as delete_error:
                                logger.warning(f"Failed to delete original task {item.content}: {delete_error}")
                        except Exception as add_error:
                            logger.error(f"Failed to create new task for {item.content}: {add_error}")
                            continue

        logger.info("Shopping list organization completed successfully!")

    except Exception as e:
        logger.error(f"Failed to organize shopping list: {e}")
        logger.exception(e)
        if 'todoist_client' in locals():
            if settings.ERROR_HANDLING_MODE in ('task', 'both'):
                create_error_task(todoist_client, f"Failed to organize shopping list: {str(e)}")
        raise

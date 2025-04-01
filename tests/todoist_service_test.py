import pytest
from unittest.mock import patch, MagicMock
from todoist_api_python.api import Task, Comment
from services.todoist_service import TodoistService


def create_mock_task(task_id, content):
    return Task(
        id=task_id,
        content=content,
        assignee_id=None,
        assigner_id=None,
        comment_count=0,
        is_completed=False,
        created_at="2024-03-30T12:00:00Z",
        creator_id="1000",
        description="Mock task",
        due=None,
        labels=[],
        order=1,
        parent_id=None,
        priority=1,
        project_id="2000",
        section_id=None,
        url=f"https://todoist.com/showTask?id={task_id}",
        duration=None
    )

def create_mock_comment(comment_id, content):
    return Comment(
        id=comment_id,
        content=content,
        attachment=None,
        posted_at="2024-03-30T12:30:00Z",
        project_id="2000",
        task_id="123"
    )

@pytest.fixture
def mock_todoist_api():
    """Fixture to mock TodoistAPI."""
    with patch("services.todoist_service.TodoistAPI") as MockAPI:
        yield MockAPI.return_value

@pytest.fixture
def todoist_service(mock_todoist_api):
    """Fixture to create an instance of TodoistService with a mocked API."""
    return TodoistService(api_key="mock_api_key")

def test_init_success(mock_todoist_api):
    """Test successful initialization."""
    mock_todoist_api.get_projects.return_value = []
    service = TodoistService(api_key="mock_api_key")
    assert isinstance(service, TodoistService)

def test_init_failure(mock_todoist_api):
    """Test initialization failure due to API error."""
    mock_todoist_api.get_projects.side_effect = Exception("API error")
    with pytest.raises(ConnectionError):
        TodoistService(api_key="mock_api_key")

def test_get_tasks_by_filter(todoist_service, mock_todoist_api):
    """Test retrieving tasks with a filter."""
    mock_task = create_mock_task("123", "Test Task")
    mock_todoist_api.get_tasks.return_value = [mock_task]

    tasks = todoist_service.get_tasks_by_filter("today")
    assert len(tasks) == 1
    assert tasks[0].id == "123"

def test_get_tasks_by_filter_empty(todoist_service, mock_todoist_api):
    """Test retrieving tasks when none match the filter."""
    mock_todoist_api.get_tasks.return_value = []
    tasks = todoist_service.get_tasks_by_filter("invalid")
    assert tasks == []

def test_get_task_by_id_success(todoist_service, mock_todoist_api):
    """Test retrieving a task by ID successfully."""
    mock_task = create_mock_task("456", "Task by ID")
    mock_todoist_api.get_task.return_value = mock_task

    task = todoist_service.get_task_by_id("456")
    assert task is not None
    assert task.id == "456"

def test_get_task_by_id_failure(todoist_service, mock_todoist_api):
    """Test handling when a task ID does not exist."""
    mock_todoist_api.get_task.side_effect = Exception("Task not found")
    task = todoist_service.get_task_by_id("999")
    assert task is None

def test_add_comment_success(todoist_service, mock_todoist_api):
    """Test adding a comment successfully."""
    mock_comment = create_mock_comment("789", "Test Comment")
    mock_todoist_api.add_comment.return_value = mock_comment

    comment = todoist_service.add_comment("123", "Hello")
    assert comment is not None
    assert comment.id == "789"

def test_add_comment_empty_content(todoist_service):
    """Test adding a comment with empty content."""
    comment = todoist_service.add_comment("123", "   ")
    assert comment is None

def test_add_comment_no_task_id(todoist_service):
    """Test adding a comment with no task ID."""
    comment = todoist_service.add_comment("", "Hello")
    assert comment is None

def test_update_task_labels_success(todoist_service, mock_todoist_api):
    """Test updating task labels successfully."""
    mock_todoist_api.update_task.return_value = True
    result = todoist_service.update_task_labels("123", ["urgent", "work"])
    assert result is True

def test_update_task_labels_failure(todoist_service, mock_todoist_api):
    """Test failure in updating task labels."""
    mock_todoist_api.update_task.side_effect = Exception("API error")
    result = todoist_service.update_task_labels("123", ["urgent"])
    assert result is False

def test_add_task_success(todoist_service, mock_todoist_api):
    """Test adding a task successfully."""
    mock_task = create_mock_task("999", "New Task")
    mock_todoist_api.add_task.return_value = mock_task

    task = todoist_service.add_task("New Task", due_string="tomorrow")
    assert task is not None
    assert task.id == "999"

def test_add_task_empty_content(todoist_service):
    """Test adding a task with empty content."""
    task = todoist_service.add_task("   ")
    assert task is None

def test_update_task_success(todoist_service, mock_todoist_api):
    """Test updating a task successfully."""
    mock_todoist_api.update_task.return_value = True
    result = todoist_service.update_task("123", content="Updated Task")
    assert result is True

def test_update_task_failure(todoist_service):
    """Test updating a task with no updates."""
    result = todoist_service.update_task("123")
    assert result is False

def test_complete_task_success(todoist_service, mock_todoist_api):
    """Test marking a task as complete successfully."""
    mock_todoist_api.close_task.return_value = True
    result = todoist_service.complete_task("123")
    assert result is True

def test_complete_task_failure(todoist_service, mock_todoist_api):
    """Test failure when marking a task as complete."""
    mock_todoist_api.close_task.side_effect = Exception("API error")
    result = todoist_service.complete_task("123")
    assert result is False


def test_delete_project_success(todoist_service, mock_todoist_api):
    """Test successfully deleting a project."""
    mock_todoist_api.delete_project.return_value = True
    result = todoist_service.delete_project("2000")
    assert result is True

def test_delete_project_failure(todoist_service, mock_todoist_api):
    """Test failure in deleting a project due to API error."""
    mock_todoist_api.delete_project.side_effect = Exception("API error")
    result = todoist_service.delete_project("2000")
    assert result is False


def test_create_project_success(todoist_service, mock_todoist_api):
    """Test successfully creating a project."""
    mock_project = MagicMock()
    mock_project.id = "3000"
    mock_project.name = "New Project"
    mock_todoist_api.add_project.return_value = mock_project

    project = todoist_service.create_project("New Project")
    assert project is not None
    assert project.id == "3000"


def test_create_project_failure(todoist_service, mock_todoist_api):
    """Test failure in creating a project."""
    mock_todoist_api.add_project.side_effect = Exception("API error")
    project = todoist_service.create_project("New Project")
    assert project is None


def test_get_sections_success(todoist_service, mock_todoist_api):
    """Test retrieving sections successfully."""
    mock_section = {"id": "4000", "name": "Section 1", "project_id": "2000"}
    mock_todoist_api.get_sections.return_value = [mock_section]

    sections = todoist_service.get_sections("2000")
    assert len(sections) == 1
    assert sections[0]["id"] == "4000"

def test_get_sections_failure(todoist_service, mock_todoist_api):
    """Test failure in retrieving sections due to API error."""
    mock_todoist_api.get_sections.side_effect = Exception("API error")
    sections = todoist_service.get_sections("2000")
    assert sections is None


def test_create_section_success(todoist_service, mock_todoist_api):
    """Test successfully creating a section."""
    mock_section = MagicMock()
    mock_section.id = "5000"
    mock_section.name = "New Section"
    mock_section.project_id = "2000"
    mock_todoist_api.add_section.return_value = mock_section

    section = todoist_service.create_section("2000", "New Section")
    assert section is not None
    assert section.id == "5000"


def test_create_section_failure(todoist_service, mock_todoist_api):
    """Test failure in creating a section."""
    mock_todoist_api.add_section.side_effect = Exception("API error")
    section = todoist_service.create_section("2000", "New Section")
    assert section is None


def test_delete_section_success(todoist_service, mock_todoist_api):
    """Test successfully deleting a section."""
    mock_todoist_api.delete_section.return_value = True
    result = todoist_service.delete_section("5000")
    assert result is True

def test_delete_section_failure(todoist_service, mock_todoist_api):
    """Test failure in deleting a section due to API error."""
    mock_todoist_api.delete_section.side_effect = Exception("API error")
    result = todoist_service.delete_section("5000")
    assert result is False


def test_get_task_comments_success(todoist_service, mock_todoist_api):
    """Test retrieving comments for a task successfully."""
    mock_comment = create_mock_comment("789", "Sample Comment")
    mock_todoist_api.get_comments.return_value = [mock_comment]

    comments = todoist_service.get_task_comments("123")
    assert len(comments) == 1
    assert comments[0].id == "789"

def test_get_task_comments_failure(todoist_service, mock_todoist_api):
    """Test failure in retrieving comments due to API error."""
    mock_todoist_api.get_comments.side_effect = Exception("API error")
    comments = todoist_service.get_task_comments("123")
    assert comments is None

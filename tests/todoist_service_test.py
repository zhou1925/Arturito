import pytest
from unittest.mock import patch, MagicMock
from todoist_api_python.api import Task, Comment
from services.todoist_service import TodoistService

# Use full required fields for Task and Comment objects.
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

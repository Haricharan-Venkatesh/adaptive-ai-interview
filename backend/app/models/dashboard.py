from pydantic import BaseModel, Field


class CodeMapNode(BaseModel):
    id: str = Field(..., description="Unique concept/node identifier")
    name: str = Field(..., description="Display name of concept or topic")
    group: str = Field(default="Concept", description="Category/group tag (e.g. Data Structures, Algorithms)")
    val: float = Field(default=10.0, description="Node relative size/importance score")
    description: str | None = Field(default=None, description="Optional description of the concept")
    mastery_score: float | None = Field(default=None, description="DKT mastery probability [0.0 - 1.0]")


class CodeMapLink(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field(default="DEPENDS_ON", description="Relationship type")
    weight: float = Field(default=1.0, description="Link weight/strength")


class CodeMapGraphResponse(BaseModel):
    status: str = Field(default="success", description="Status flag: 'success', 'empty', or 'error'")
    nodes: list[CodeMapNode] = Field(default_factory=list, description="List of graph nodes")
    links: list[CodeMapLink] = Field(default_factory=list, description="List of graph relationships")
    message: str | None = Field(default=None, description="Detailed status message or error details")
    count_nodes: int = Field(default=0, description="Total node count")
    count_links: int = Field(default=0, description="Total link count")

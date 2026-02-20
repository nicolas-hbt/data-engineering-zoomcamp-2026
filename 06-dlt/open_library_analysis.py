"""
marimo notebook to visualize top 10 authors by book count from Open Library data.
Uses ibis for data access via dlt dataset.
"""

import marimo

__generated_with = "0.19.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import dlt
    import ibis
    import pandas as pd
    import plotly.express as px
    import marimo as mo

    return dlt, ibis, mo, px


@app.cell
def _(dlt):
    # Connect to the dlt pipeline and get ibis connection
    pipeline = dlt.pipeline(
        pipeline_name='open_library_pipeline',
        destination='duckdb'
    )
    dataset = pipeline.dataset()
    ibis_conn = dataset.ibis()
    return (ibis_conn,)


@app.cell
def _(ibis, ibis_conn):
    # Get the books__authors table
    authors_table = ibis_conn.table("books__authors")

    # Count books per author
    # Group by author name and count distinct book references
    # The _dlt_parent_id links back to the parent book
    author_counts = (
        authors_table
        .group_by("name")
        .aggregate(book_count=authors_table._dlt_parent_id.nunique())
        .order_by(ibis.desc("book_count"))
        .limit(10)
    )

    # Execute the query and convert to pandas
    top_authors_df = author_counts.to_pandas()
    return (top_authors_df,)


@app.cell
def _(mo):
    # Display the data table
    mo.md("""
    ## Top 10 Authors by Book Count
    """)
    return


@app.cell
def _(mo, top_authors_df):
    # Show the data table
    mo.ui.table(top_authors_df)
    return


@app.cell
def _(mo, px, top_authors_df):
    # Create a bar chart visualization
    if len(top_authors_df) > 0:
        fig = px.bar(
            top_authors_df,
            x='book_count',
            y='name',
            orientation='h',
            title='Top 10 Authors by Book Count',
            labels={'book_count': 'Number of Books', 'name': 'Author Name'},
            color='book_count',
            color_continuous_scale='Blues'
        )

        # Update layout for better readability
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500,
            showlegend=False
        )

        fig
    else:
        mo.md("⚠️ No author data available. Please load more books into the pipeline.")
    return


@app.cell
def _(mo):
    mo.md("""
    ### Notes
    - This visualization shows the top 10 authors based on the number of books in the dataset
    - Data is accessed via ibis through the dlt dataset connection
    - The `books__authors` table contains normalized author information linked to books
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

export const paginationLabels = {
  nextPageLabel: 'Next page',
  previousPageLabel: 'Previous page',
  pageLabel: pageNumber => `Page ${pageNumber} of all pages`,
};

const headerLabel = (title, sorted, descending) => {
  return `${title}, ${sorted ? `sorted ${descending ? 'descending' : 'ascending'}` : 'not sorted'}.`;
};

export const addColumnSortLabels = columns =>
  columns.map(col => ({
    ariaLabel:
      col.sortingField || col.sortingComparator
        ? sortState => headerLabel(col.header, sortState.sorted, sortState.descending)
        : undefined,
    ...col,
  }));

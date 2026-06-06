import {
    get,
    post,
    remove
}
from "./api.js";

export async function getDatasets(
    projectId
){

    return await get(
        `/projects/${projectId}/datasets`
    );
}

export async function createDataset(
    projectId
){

    return await post(
        `/projects/${projectId}/datasets`,
        {}
    );
}

export async function deleteDataset(
    datasetId
){

    return await remove(
        `/datasets/${datasetId}`
    );
}
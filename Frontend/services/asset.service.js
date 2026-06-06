import {
    apiGet,
    apiPost
}
from "./api.js";

export async function getAssets(
    datasetId
){

    return await apiGet(
        `/datasets/${datasetId}/assets`
    );
}
import {
    get,
    post,
    put,
    remove
}
from "./api.js";

export async function getProjects(){

    return await get(
        "/projects"
    );
}

export async function getProject(
    projectId
){

    return await get(
        `/projects/${projectId}`
    );
}

export async function createProject(
    payload
){

    return await post(
        "/projects",
        payload
    );
}

export async function updateProject(
    projectId,
    payload
){

    return await put(
        `/projects/${projectId}`,
        payload
    );
}

export async function deleteProject(
    projectId
){

    return await remove(
        `/projects/${projectId}`
    );
}
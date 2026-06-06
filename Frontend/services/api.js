const API_BASE_URL="http://localhost:8000/api/v1";

async function request(
    endpoint,
    options={}
){

    const response=await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            headers:{
                "Content-Type":"application/json"
            },
            ...options
        }
    );

    if(!response.ok){

        let message="Request Failed";

        try{

            const error=await response.json();

            message=
                error.detail ||
                message;

        }
        catch{}

        throw new Error(message);
    }

    if(response.status===204){
        return null;
    }

    return await response.json();
}

export async function get(
    endpoint
){

    return request(
        endpoint,
        {
            method:"GET"
        }
    );
}

export async function post(
    endpoint,
    data
){

    return request(
        endpoint,
        {
            method:"POST",
            body:JSON.stringify(data)
        }
    );
}

export async function put(
    endpoint,
    data
){

    return request(
        endpoint,
        {
            method:"PUT",
            body:JSON.stringify(data)
        }
    );
}

export async function remove(
    endpoint
){

    return request(
        endpoint,
        {
            method:"DELETE"
        }
    );
}
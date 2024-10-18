const hash = "d49cf7fc88dfb440638ea6e74ed8c528468ac73ba661ce612fe39e9cd701bfc1";
const date = new Date()

async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hash = await crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("");
}

async function getAuth() {
    const authValue = hash + await hashPassword(date.getUTCDate().toString());
    return authValue;
}

// async function Auth() {
//     try {
//         const auth = await getAuth();
        
//         const response = await fetch('/verify-auth', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ auth })
//         });

//         if (response.status === 401) {
//             window.location.href = '/login';
//         } else {
//             console.log("User is authenticated");
//         }
//     } catch (error) {
//         console.error("Error during authentication:", error);
//     }
// }
// menymp
//  Feb 3 2024
//
// contains utilities for session


export const isSessionActive = () => {
    return sessionStorage.getItem("userId") && sessionStorage.getItem("user")
}